"""設定ダイアログ — APIプロバイダー切り替え + API タブ + プロンプトタブ."""

from __future__ import annotations

from dataclasses import replace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import ApiProvider, AppConfig, DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_MESSAGE_TEMPLATE
from src.ui.toggle_switch import ToggleSwitch


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._init_ui()
        self._load_values()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowTitle("設定")
        self.setMinimumSize(500, 480)
        self.resize(560, 540)

        root = QVBoxLayout(self)

        root.addLayout(self._build_provider_row())
        root.addSpacing(8)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_api_tab(), "API")
        self._prompt_tab = self._build_prompt_tab()
        self._tabs.addTab(self._prompt_tab, "プロンプト")
        root.addWidget(self._tabs)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        root.addWidget(btn_box)

    # --- プロバイダー切替行 ---

    def _build_provider_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._label_openai = QLabel("OpenAI互換API")
        self._label_openai.setStyleSheet("font-weight: bold;")

        self._provider_toggle = ToggleSwitch()
        self._provider_toggle.toggled.connect(self._on_provider_changed)

        self._label_google = QLabel("Google翻訳")
        self._label_google.setStyleSheet("color: #888;")

        row.addStretch()
        row.addWidget(self._label_openai)
        row.addSpacing(8)
        row.addWidget(self._provider_toggle)
        row.addSpacing(8)
        row.addWidget(self._label_google)
        row.addStretch()

        return row

    def _on_provider_changed(self, is_google: bool) -> None:
        if is_google:
            self._label_openai.setStyleSheet("color: #888;")
            self._label_google.setStyleSheet("font-weight: bold;")
        else:
            self._label_openai.setStyleSheet("font-weight: bold;")
            self._label_google.setStyleSheet("color: #888;")

        self._api_url_edit.setEnabled(not is_google)
        self._model_edit.setEnabled(not is_google)
        self._temperature_spin.setEnabled(not is_google)
        self._max_tokens_spin.setEnabled(not is_google)

        self._tabs.setTabEnabled(1, not is_google)

    # --- API タブ ---

    def _build_api_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._api_url_edit = QLineEdit()
        self._api_url_edit.setPlaceholderText("http://127.0.0.1:8080")
        form.addRow("API URL:", self._api_url_edit)

        self._model_edit = QLineEdit()
        self._model_edit.setPlaceholderText("(空 = サーバーデフォルト)")
        form.addRow("モデル名:", self._model_edit)

        self._temperature_spin = QDoubleSpinBox()
        self._temperature_spin.setRange(0.0, 2.0)
        self._temperature_spin.setSingleStep(0.1)
        self._temperature_spin.setDecimals(2)
        form.addRow("Temperature:", self._temperature_spin)

        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(1, 65536)
        form.addRow("Max Tokens:", self._max_tokens_spin)

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(1, 600)
        self._timeout_spin.setSuffix(" 秒")
        form.addRow("タイムアウト:", self._timeout_spin)

        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(100)
        self._opacity_label = QLabel("100%")
        self._opacity_label.setFixedWidth(36)
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%"),
        )
        opacity_row.addWidget(self._opacity_slider)
        opacity_row.addWidget(self._opacity_label)
        form.addRow("透明度:", opacity_row)

        return page

    # --- プロンプトタブ ---

    def _build_prompt_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        placeholder_label = QLabel(
            "プレースホルダー: "
            "<code>{{source_language}}</code>  "
            "<code>{{target_language}}</code>  "
            "<code>{{input_text}}</code>",
        )
        placeholder_label.setTextFormat(Qt.TextFormat.RichText)
        placeholder_label.setWordWrap(True)
        layout.addWidget(placeholder_label)

        layout.addWidget(QLabel("システムプロンプト:"))
        self._system_prompt_edit = QPlainTextEdit()
        self._system_prompt_edit.setMinimumHeight(100)
        layout.addWidget(self._system_prompt_edit, 2)

        layout.addWidget(QLabel("ユーザーメッセージテンプレート:"))
        self._user_msg_edit = QPlainTextEdit()
        self._user_msg_edit.setMinimumHeight(80)
        layout.addWidget(self._user_msg_edit, 1)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("デフォルトに戻す")
        reset_btn.clicked.connect(self._reset_prompts)
        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        layout.addLayout(btn_row)

        return page

    # ------------------------------------------------------------------
    # 値の読み書き
    # ------------------------------------------------------------------

    def _load_values(self) -> None:
        is_google = self._config.provider == ApiProvider.GOOGLE
        self._provider_toggle.setChecked(is_google)
        self._on_provider_changed(is_google)

        self._api_url_edit.setText(self._config.api_url)
        self._model_edit.setText(self._config.model)
        self._temperature_spin.setValue(self._config.temperature)
        self._max_tokens_spin.setValue(self._config.max_tokens)
        self._timeout_spin.setValue(self._config.timeout)
        opacity_pct = max(20, min(100, int(self._config.opacity * 100)))
        self._opacity_slider.setValue(opacity_pct)
        self._system_prompt_edit.setPlainText(self._config.system_prompt)
        self._user_msg_edit.setPlainText(self._config.user_message_template)

    def get_config(self) -> AppConfig:
        provider = ApiProvider.GOOGLE if self._provider_toggle.isChecked() else ApiProvider.OPENAI
        return replace(
            self._config,
            api_provider=provider.value,
            api_url=self._api_url_edit.text().strip() or self._config.api_url,
            model=self._model_edit.text().strip(),
            temperature=self._temperature_spin.value(),
            max_tokens=self._max_tokens_spin.value(),
            timeout=self._timeout_spin.value(),
            opacity=self._opacity_slider.value() / 100.0,
            system_prompt=self._system_prompt_edit.toPlainText(),
            user_message_template=self._user_msg_edit.toPlainText(),
        )

    def _reset_prompts(self) -> None:
        self._system_prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT)
        self._user_msg_edit.setPlainText(DEFAULT_USER_MESSAGE_TEMPLATE)
