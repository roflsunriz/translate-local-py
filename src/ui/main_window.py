"""メインウィンドウ — 翻訳画面."""

from __future__ import annotations

import logging
from typing import cast

from PyQt6.QtCore import QByteArray, QSize, QTimer, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence, QResizeEvent, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.config import (
    PROVIDER_ORDER,
    ApiProvider,
    AppConfig,
    ICONS_DIR,
    PRESET_LANGUAGES,
    PROVIDER_LABELS,
    RESOURCES_DIR,
)
from src.translator import TranslationManager
from src.ui.settings_dialog import SettingsDialog


logger = logging.getLogger(__name__)


def _icon(name: str) -> QIcon:
    return QIcon(str(ICONS_DIR / name))


class AutoResizePlainTextEdit(QPlainTextEdit):
    """内容に応じて高さが自動調整されるテキストエリア.

    デフォルトは1行分の高さで、テキストが増えると _MAX_LINES まで伸びる。
    それ以上はスクロールで対応する。
    """

    _MIN_LINES = 1
    _MAX_LINES = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_height = 0
        self._adjusting = False

        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.textChanged.connect(self._schedule_adjust)

        line_h = self.fontMetrics().lineSpacing()
        doc = self.document()
        doc_margin = int(doc.documentMargin()) if doc is not None else 0
        frame = self.frameWidth() * 2
        initial = line_h * self._MIN_LINES + doc_margin * 2 + frame
        self._current_height = initial
        self.setFixedHeight(initial)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if not self._adjusting:
            self._schedule_adjust()

    def _schedule_adjust(self) -> None:
        QTimer.singleShot(0, self._adjust_height)

    def _count_visual_lines(self) -> int:
        doc = self.document()
        if doc is None:
            return 1
        total = 0
        block = doc.begin()
        while block.isValid():
            block_layout = block.layout()
            if block_layout is not None and block_layout.lineCount() > 0:
                total += block_layout.lineCount()
            else:
                total += 1
            block = block.next()
        return max(1, total)

    def _adjust_height(self) -> None:
        if self._adjusting:
            return
        self._adjusting = True
        try:
            visual_lines = self._count_visual_lines()
            clamped = max(self._MIN_LINES, min(self._MAX_LINES, visual_lines))

            line_h = self.fontMetrics().lineSpacing()
            doc = self.document()
            doc_margin = int(doc.documentMargin()) if doc is not None else 0
            frame = self.frameWidth() * 2

            new_height = line_h * clamped + doc_margin * 2 + frame
            if new_height == self._current_height:
                return

            old_height = self._current_height
            self._current_height = new_height
            self.setFixedHeight(new_height)

            window = self.window()
            if window is not None and window.isVisible() and old_height > 0:
                delta = new_height - old_height
                window.resize(window.width(), window.height() + delta)
        finally:
            self._adjusting = False


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._config = AppConfig.load()
        self._translator = TranslationManager(self)

        self._init_ui()
        self._connect_signals()
        self._apply_config()
        self.adjustSize()

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowTitle("LLM Translator")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "icon.ico")))
        self.setMinimumWidth(480)

        # --- ツールバー ---
        toolbar = QToolBar("メイン")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        self._pin_action = QAction(_icon("pin.svg"), "最前面", self)
        self._pin_action.setCheckable(True)
        self._pin_action.setToolTip("ウィンドウを常に最前面に表示")
        toolbar.addAction(self._pin_action)

        toolbar.addSeparator()

        self._settings_action = QAction(_icon("settings.svg"), "設定", self)
        self._settings_action.setToolTip("設定ダイアログを開く")
        toolbar.addAction(self._settings_action)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel(" モード:"))
        self._toolbar_provider_group = QButtonGroup(self)
        self._toolbar_provider_group.setExclusive(True)
        self._toolbar_provider_checks: dict[ApiProvider, QCheckBox] = {}
        for provider in PROVIDER_ORDER:
            checkbox = QCheckBox(PROVIDER_LABELS[provider])
            checkbox.setToolTip(f"{PROVIDER_LABELS[provider]} に切り替え")
            self._toolbar_provider_group.addButton(checkbox)
            self._toolbar_provider_checks[provider] = checkbox
            toolbar.addWidget(checkbox)

        toolbar.addSeparator()

        opacity_label = QLabel(" 透明度:")
        toolbar.addWidget(opacity_label)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.setFixedWidth(100)
        self._opacity_slider.setToolTip("ウィンドウの透明度 (20%–100%)")
        toolbar.addWidget(self._opacity_slider)
        self._opacity_value_label = QLabel("100%")
        self._opacity_value_label.setFixedWidth(36)
        toolbar.addWidget(self._opacity_value_label)

        # --- 中央ウィジェット ---
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 4, 8, 4)

        # 言語選択バー
        lang_bar = QHBoxLayout()

        self._source_combo = self._make_lang_combo()
        self._swap_btn = QPushButton(_icon("swap.svg"), "")
        self._swap_btn.setFixedWidth(36)
        self._swap_btn.setToolTip("言語を入れ替え")
        self._target_combo = self._make_lang_combo()

        lang_bar.addWidget(self._source_combo, 1)
        lang_bar.addWidget(self._swap_btn)
        lang_bar.addWidget(self._target_combo, 1)
        layout.addLayout(lang_bar)

        # テキストエリア (内容に応じて自動リサイズ)
        self._source_edit = AutoResizePlainTextEdit()
        self._source_edit.setPlaceholderText("翻訳したいテキストを入力…")
        layout.addWidget(self._source_edit)

        self._target_edit = AutoResizePlainTextEdit()
        self._target_edit.setPlaceholderText("翻訳結果がここに表示されます")
        layout.addWidget(self._target_edit)

        layout.addStretch(1)

        # ボタンバー
        btn_bar = QHBoxLayout()

        self._translate_btn = QPushButton(_icon("translate.svg"), "翻訳 (Ctrl+Enter)")
        self._translate_btn.setDefault(True)

        self._copy_btn = QPushButton(_icon("copy.svg"), "コピー")
        self._copy_btn.setToolTip("翻訳結果をクリップボードにコピー")

        self._clear_btn = QPushButton(_icon("clear.svg"), "クリア")
        self._clear_btn.setToolTip("入力と結果をクリア")

        btn_bar.addWidget(self._translate_btn)
        btn_bar.addWidget(self._copy_btn)
        btn_bar.addWidget(self._clear_btn)
        layout.addLayout(btn_bar)

        # ステータスバー
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._provider_label = QLabel()
        self._status_bar.addPermanentWidget(self._provider_label)
        self._update_provider_label()

        self._status_bar.showMessage("準備完了")

        # ショートカット
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_translate)

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _update_provider_label(self) -> None:
        self._provider_label.setText(self._config.provider_label())

    def _sync_toolbar_provider_checks(self) -> None:
        for provider, checkbox in self._toolbar_provider_checks.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(provider == self._config.provider)
            checkbox.blockSignals(False)

    @staticmethod
    def _make_lang_combo() -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        for display_name, code in PRESET_LANGUAGES:
            combo.addItem(f"{display_name} ({code})", code)
        combo.setCurrentIndex(-1)
        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText("言語コード")
        return combo

    def _current_lang_code(self, combo: QComboBox) -> str:
        """コンボボックスから言語コードを取得する.

        プリセット選択時は userData、手入力時はテキストをそのまま使う。
        """
        idx = combo.currentIndex()
        if idx >= 0:
            data = combo.itemData(idx)
            if data is not None:
                return str(data)
        return combo.currentText().strip()

    def _set_lang_combo(self, combo: QComboBox, code: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == code:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentText(code)

    # ------------------------------------------------------------------
    # シグナル接続
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._pin_action.toggled.connect(self._on_pin_toggled)
        self._settings_action.triggered.connect(self._on_settings)
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self._swap_btn.clicked.connect(self._on_swap_languages)
        self._translate_btn.clicked.connect(self._on_translate)
        self._copy_btn.clicked.connect(self._on_copy)
        self._clear_btn.clicked.connect(self._on_clear)
        self._translator.translation_finished.connect(self._on_translation_finished)
        self._translator.translation_error.connect(self._on_translation_error)
        for provider, checkbox in self._toolbar_provider_checks.items():
            checkbox.toggled.connect(
                lambda checked, p=provider: self._on_toolbar_provider_changed(p, checked),
            )

    # ------------------------------------------------------------------
    # 設定の適用・保存
    # ------------------------------------------------------------------

    def _apply_config(self) -> None:
        self._set_lang_combo(self._source_combo, self._config.source_lang)
        self._set_lang_combo(self._target_combo, self._config.target_lang)

        self._pin_action.setChecked(self._config.always_on_top)

        self._sync_toolbar_provider_checks()

        opacity_pct = max(20, min(100, int(self._config.opacity * 100)))
        self._opacity_slider.setValue(opacity_pct)
        self.setWindowOpacity(self._config.opacity)

        if self._config.window_geometry:
            try:
                geo = QByteArray.fromBase64(self._config.window_geometry.encode("ascii"))
                self.restoreGeometry(geo)
            except Exception:  # noqa: BLE001
                pass

    def _save_config(self) -> None:
        self._config.source_lang = self._current_lang_code(self._source_combo)
        self._config.target_lang = self._current_lang_code(self._target_combo)
        self._config.always_on_top = self._pin_action.isChecked()
        self._config.opacity = self._opacity_slider.value() / 100.0
        self._config.window_geometry = self.saveGeometry().toBase64().data().decode("ascii")
        self._config.save()

    # ------------------------------------------------------------------
    # イベントハンドラ
    # ------------------------------------------------------------------

    def _on_pin_toggled(self, checked: bool) -> None:
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _on_toolbar_provider_changed(self, provider: ApiProvider, checked: bool) -> None:
        if not checked:
            return
        self._config.api_provider = provider.value
        self._update_provider_label()
        self._save_config()

    def _on_opacity_changed(self, value: int) -> None:
        self._opacity_value_label.setText(f"{value}%")
        self.setWindowOpacity(value / 100.0)

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self._config, self)
        if dlg.exec():
            self._config = dlg.get_config()
            opacity_pct = max(20, min(100, int(self._config.opacity * 100)))
            self._opacity_slider.setValue(opacity_pct)
            self.setWindowOpacity(self._config.opacity)
            self._sync_toolbar_provider_checks()
            self._update_provider_label()
            self._save_config()

    def _on_swap_languages(self) -> None:
        src_code = self._current_lang_code(self._source_combo)
        tgt_code = self._current_lang_code(self._target_combo)
        self._set_lang_combo(self._source_combo, tgt_code)
        self._set_lang_combo(self._target_combo, src_code)

    def _on_translate(self) -> None:
        source_text = self._source_edit.toPlainText().strip()
        if not source_text:
            self._status_bar.showMessage("テキストを入力してください")
            return

        if self._translator.is_running:
            self._status_bar.showMessage("翻訳中です…")
            return

        source_lang = self._current_lang_code(self._source_combo)
        target_lang = self._current_lang_code(self._target_combo)

        if not source_lang or not target_lang:
            self._status_bar.showMessage("言語を選択してください")
            return

        self._translate_btn.setEnabled(False)
        self._status_bar.showMessage("翻訳中…")
        self._translator.translate(self._config, source_text, source_lang, target_lang)

    def _on_translation_finished(self, result: str, elapsed: float) -> None:
        self._target_edit.setPlainText(result)
        self._translate_btn.setEnabled(True)
        self._status_bar.showMessage(f"翻訳完了 ({elapsed:.1f}秒)")

    def _on_translation_error(self, message: str) -> None:
        self._target_edit.setPlainText("")
        self._translate_btn.setEnabled(True)
        self._status_bar.showMessage(message)

    def _on_copy(self) -> None:
        text = self._target_edit.toPlainText()
        if not text:
            self._status_bar.showMessage("コピーするテキストがありません")
            return
        clipboard = cast(QApplication, QApplication.instance()).clipboard()
        if clipboard is not None:
            clipboard.setText(text)
        self._copy_btn.setText("コピー済み!")
        QTimer.singleShot(1500, self._reset_copy_btn_text)
        self._status_bar.showMessage("クリップボードにコピーしました")

    def _reset_copy_btn_text(self) -> None:
        self._copy_btn.setText("コピー")

    def _on_clear(self) -> None:
        self._source_edit.clear()
        self._target_edit.clear()
        self._status_bar.showMessage("クリア")

    # ------------------------------------------------------------------
    # ウィンドウイベント
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent | None) -> None:  # type: ignore[override]
        self._save_config()
        super().closeEvent(event)
