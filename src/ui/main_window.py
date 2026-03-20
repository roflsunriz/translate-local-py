"""メインウィンドウ — 翻訳画面."""

from __future__ import annotations

import logging
from typing import cast

from PyQt6.QtCore import QByteArray, QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.config import AppConfig, PRESET_LANGUAGES
from src.translator import TranslationManager
from src.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._config = AppConfig.load()
        self._translator = TranslationManager(self)

        self._init_ui()
        self._connect_signals()
        self._apply_config()

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowTitle("LLM Translator")
        self.setMinimumSize(480, 400)
        self.resize(560, 520)

        # --- ツールバー ---
        toolbar = QToolBar("メイン")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._pin_action = QAction("📌 最前面", self)
        self._pin_action.setCheckable(True)
        self._pin_action.setToolTip("ウィンドウを常に最前面に表示")
        toolbar.addAction(self._pin_action)

        toolbar.addSeparator()

        self._settings_action = QAction("⚙ 設定", self)
        self._settings_action.setToolTip("設定ダイアログを開く")
        toolbar.addAction(self._settings_action)

        # --- 中央ウィジェット ---
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 4, 8, 4)

        # 言語選択バー
        lang_bar = QHBoxLayout()

        self._source_combo = self._make_lang_combo()
        self._swap_btn = QPushButton("⇄")
        self._swap_btn.setFixedWidth(36)
        self._swap_btn.setToolTip("言語を入れ替え")
        self._target_combo = self._make_lang_combo()

        lang_bar.addWidget(self._source_combo, 1)
        lang_bar.addWidget(self._swap_btn)
        lang_bar.addWidget(self._target_combo, 1)
        layout.addLayout(lang_bar)

        # テキストエリア (スプリッター)
        splitter = QSplitter(Qt.Orientation.Vertical)

        self._source_edit = QPlainTextEdit()
        self._source_edit.setPlaceholderText("翻訳したいテキストを入力…")
        splitter.addWidget(self._source_edit)

        self._target_edit = QPlainTextEdit()
        self._target_edit.setPlaceholderText("翻訳結果がここに表示されます")
        splitter.addWidget(self._target_edit)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        # ボタンバー
        btn_bar = QHBoxLayout()

        self._translate_btn = QPushButton("翻訳 (Ctrl+Enter)")
        self._translate_btn.setDefault(True)

        self._copy_btn = QPushButton("コピー")
        self._copy_btn.setToolTip("翻訳結果をクリップボードにコピー")

        self._clear_btn = QPushButton("クリア")
        self._clear_btn.setToolTip("入力と結果をクリア")

        btn_bar.addWidget(self._translate_btn)
        btn_bar.addWidget(self._copy_btn)
        btn_bar.addWidget(self._clear_btn)
        layout.addLayout(btn_bar)

        # ステータスバー
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("準備完了")

        # ショートカット
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_translate)

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    @staticmethod
    def _make_lang_combo() -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        for display_name, code in PRESET_LANGUAGES:
            combo.addItem(f"{display_name} ({code})", code)
        combo.setCurrentIndex(-1)
        combo.lineEdit().setPlaceholderText("言語コード")
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
        self._swap_btn.clicked.connect(self._on_swap_languages)
        self._translate_btn.clicked.connect(self._on_translate)
        self._copy_btn.clicked.connect(self._on_copy)
        self._clear_btn.clicked.connect(self._on_clear)
        self._translator.translation_finished.connect(self._on_translation_finished)
        self._translator.translation_error.connect(self._on_translation_error)

    # ------------------------------------------------------------------
    # 設定の適用・保存
    # ------------------------------------------------------------------

    def _apply_config(self) -> None:
        self._set_lang_combo(self._source_combo, self._config.source_lang)
        self._set_lang_combo(self._target_combo, self._config.target_lang)

        self._pin_action.setChecked(self._config.always_on_top)

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
        self._config.window_geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
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

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self._config, self)
        if dlg.exec():
            self._config = dlg.get_config()
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
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("コピー"))
        self._status_bar.showMessage("クリップボードにコピーしました")

    def _on_clear(self) -> None:
        self._source_edit.clear()
        self._target_edit.clear()
        self._status_bar.showMessage("クリア")

    # ------------------------------------------------------------------
    # ウィンドウイベント
    # ------------------------------------------------------------------

    def closeEvent(self, event: "QCloseEvent | None") -> None:  # type: ignore[override]
        self._save_config()
        super().closeEvent(event)
