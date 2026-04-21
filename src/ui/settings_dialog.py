"""設定ダイアログ — モード選択 + API タブ + プロンプトタブ."""

from __future__ import annotations

from dataclasses import replace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import (
    CEREBRAS_MODELS,
    PROVIDER_ORDER,
    SAKURA_MODELS,
    ApiProvider,
    AppConfig,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_MESSAGE_TEMPLATE,
    PROVIDER_LABELS,
)


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._provider_checks: dict[ApiProvider, QCheckBox] = {}
        self._page_indexes: dict[ApiProvider, int] = {}
        self._init_ui()
        self._load_values()

    def _init_ui(self) -> None:
        self.setWindowTitle("設定")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)

        root = QVBoxLayout(self)

        root.addWidget(self._build_provider_group())
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

    def _build_provider_group(self) -> QGroupBox:
        group = QGroupBox("モード")
        layout = QGridLayout(group)

        self._provider_group = QButtonGroup(self)
        self._provider_group.setExclusive(True)
        self._provider_group.idToggled.connect(self._on_provider_changed)

        for index, provider in enumerate(PROVIDER_ORDER):
            checkbox = QCheckBox(PROVIDER_LABELS[provider])
            self._provider_group.addButton(checkbox, index)
            self._provider_checks[provider] = checkbox
            layout.addWidget(checkbox, index // 3, index % 3)

        return group

    def _build_api_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        self._provider_pages = QStackedWidget()
        self._page_indexes[ApiProvider.LOCAL] = self._provider_pages.addWidget(self._build_local_page())
        self._page_indexes[ApiProvider.GOOGLE] = self._provider_pages.addWidget(self._build_google_page())
        self._page_indexes[ApiProvider.OPENROUTER] = self._provider_pages.addWidget(self._build_openrouter_page())
        self._page_indexes[ApiProvider.CEREBRAS] = self._provider_pages.addWidget(self._build_cerebras_page())
        self._page_indexes[ApiProvider.SAKURA] = self._provider_pages.addWidget(self._build_sakura_page())
        self._page_indexes[ApiProvider.CUSTOM] = self._provider_pages.addWidget(self._build_custom_page())
        layout.addWidget(self._provider_pages)

        common_group = QGroupBox("共通設定")
        form = QFormLayout(common_group)

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

        layout.addWidget(common_group)
        return page

    def _build_local_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._local_api_url_edit = QLineEdit()
        self._local_api_url_edit.setPlaceholderText("http://127.0.0.1:8080")
        form.addRow("ローカルAPI URL:", self._local_api_url_edit)

        note = QLabel("ローカルでは API キーとモデル名の入力は不要です。")
        note.setWordWrap(True)
        form.addRow("", note)
        return page

    def _build_google_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("Google翻訳では API エンドポイント、API キー、モデル設定は不要です。")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch(1)
        return page

    def _build_openrouter_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        endpoint = QLabel("https://openrouter.ai/api/v1/chat/completions")
        endpoint.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("API URL:", endpoint)

        self._openrouter_api_key_edit = QLineEdit()
        self._openrouter_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API キー:", self._openrouter_api_key_edit)

        self._openrouter_model_edit = QLineEdit()
        self._openrouter_model_edit.setPlaceholderText("モデル名を入力")
        form.addRow("モデル名:", self._openrouter_model_edit)
        return page

    def _build_cerebras_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        endpoint = QLabel("https://api.cerebras.ai/v1/chat/completions")
        endpoint.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("API URL:", endpoint)

        self._cerebras_api_key_edit = QLineEdit()
        self._cerebras_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API キー:", self._cerebras_api_key_edit)

        self._cerebras_model_combo = QComboBox()
        for model in CEREBRAS_MODELS:
            self._cerebras_model_combo.addItem(model)
        form.addRow("モデル:", self._cerebras_model_combo)
        return page

    def _build_sakura_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        endpoint = QLabel("https://api.ai.sakura.ad.jp/v1/chat/completions")
        endpoint.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("API URL:", endpoint)

        self._sakura_api_key_edit = QLineEdit()
        self._sakura_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API キー:", self._sakura_api_key_edit)

        self._sakura_model_combo = QComboBox()
        for model in SAKURA_MODELS:
            self._sakura_model_combo.addItem(model)
        form.addRow("モデル:", self._sakura_model_combo)
        return page

    def _build_custom_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._custom_api_url_edit = QLineEdit()
        self._custom_api_url_edit.setPlaceholderText("https://example.com/v1/chat/completions")
        form.addRow("API URL:", self._custom_api_url_edit)

        self._custom_api_key_edit = QLineEdit()
        self._custom_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API キー:", self._custom_api_key_edit)

        self._custom_model_edit = QLineEdit()
        self._custom_model_edit.setPlaceholderText("モデル名を入力")
        form.addRow("モデル名:", self._custom_model_edit)
        return page

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

    def _selected_provider(self) -> ApiProvider:
        for provider, checkbox in self._provider_checks.items():
            if checkbox.isChecked():
                return provider
        return ApiProvider.LOCAL

    def _on_provider_changed(self, button_id: int, checked: bool) -> None:
        if not checked:
            return
        provider = PROVIDER_ORDER[button_id]
        self._provider_pages.setCurrentIndex(self._page_indexes[provider])
        self._tabs.setTabEnabled(1, provider != ApiProvider.GOOGLE)

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
            return
        combo.addItem(value)
        combo.setCurrentIndex(combo.count() - 1)

    def _load_values(self) -> None:
        self._provider_checks[self._config.provider].setChecked(True)
        self._provider_pages.setCurrentIndex(self._page_indexes[self._config.provider])
        self._tabs.setTabEnabled(1, self._config.provider != ApiProvider.GOOGLE)

        self._local_api_url_edit.setText(self._config.local_api_url)
        self._openrouter_api_key_edit.setText(self._config.openrouter_api_key)
        self._openrouter_model_edit.setText(self._config.openrouter_model)
        self._cerebras_api_key_edit.setText(self._config.cerebras_api_key)
        self._set_combo_value(self._cerebras_model_combo, self._config.cerebras_model)
        self._sakura_api_key_edit.setText(self._config.sakura_api_key)
        self._set_combo_value(self._sakura_model_combo, self._config.sakura_model)
        self._custom_api_url_edit.setText(self._config.custom_api_url)
        self._custom_api_key_edit.setText(self._config.custom_api_key)
        self._custom_model_edit.setText(self._config.custom_model)

        self._temperature_spin.setValue(self._config.temperature)
        self._max_tokens_spin.setValue(self._config.max_tokens)
        self._timeout_spin.setValue(self._config.timeout)
        opacity_pct = max(20, min(100, int(self._config.opacity * 100)))
        self._opacity_slider.setValue(opacity_pct)
        self._system_prompt_edit.setPlainText(self._config.system_prompt)
        self._user_msg_edit.setPlainText(self._config.user_message_template)

    def get_config(self) -> AppConfig:
        return replace(
            self._config,
            api_provider=self._selected_provider().value,
            local_api_url=self._local_api_url_edit.text().strip() or self._config.local_api_url,
            openrouter_api_key=self._openrouter_api_key_edit.text().strip(),
            openrouter_model=self._openrouter_model_edit.text().strip(),
            cerebras_api_key=self._cerebras_api_key_edit.text().strip(),
            cerebras_model=self._cerebras_model_combo.currentText().strip(),
            sakura_api_key=self._sakura_api_key_edit.text().strip(),
            sakura_model=self._sakura_model_combo.currentText().strip(),
            custom_api_url=self._custom_api_url_edit.text().strip(),
            custom_api_key=self._custom_api_key_edit.text().strip(),
            custom_model=self._custom_model_edit.text().strip(),
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
