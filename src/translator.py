"""翻訳 API クライアント — 複数プロバイダー / Google 非公式 + QThread ワーカー."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.config import ApiProvider, AppConfig

logger = logging.getLogger(__name__)


def expand_template(
    template: str,
    *,
    source_language: str,
    target_language: str,
    input_text: str = "",
) -> str:
    """Mustache 風プレースホルダーを値で置換する."""
    result = template.replace("{{source_language}}", source_language)
    result = result.replace("{{target_language}}", target_language)
    result = result.replace("{{input_text}}", input_text)
    return result


def _resolve_api_settings(config: AppConfig) -> tuple[str, str, str]:
    provider = config.provider
    if provider == ApiProvider.LOCAL:
        endpoint = f"{config.local_api_url.rstrip('/')}/v1/chat/completions"
        return endpoint, "", ""
    if provider == ApiProvider.OPENROUTER:
        return (
            "https://openrouter.ai/api/v1/chat/completions",
            config.openrouter_model.strip(),
            config.openrouter_api_key.strip(),
        )
    if provider == ApiProvider.CEREBRAS:
        return (
            "https://api.cerebras.ai/v1/chat/completions",
            config.cerebras_model.strip(),
            config.cerebras_api_key.strip(),
        )
    if provider == ApiProvider.SAKURA:
        return (
            "https://api.ai.sakura.ad.jp/v1/chat/completions",
            config.sakura_model.strip(),
            config.sakura_api_key.strip(),
        )
    if provider == ApiProvider.CUSTOM:
        return (
            config.custom_api_url.strip(),
            config.custom_model.strip(),
            config.custom_api_key.strip(),
        )
    raise ValueError(f"Unsupported provider: {provider.value}")


def _validate_api_settings(config: AppConfig, endpoint: str, model: str, api_key: str) -> None:
    provider = config.provider
    if provider == ApiProvider.OPENROUTER:
        if not api_key:
            raise ValueError("OpenRouter の API キーを入力してください。")
        if not model:
            raise ValueError("OpenRouter のモデル名を入力してください。")
    elif provider == ApiProvider.CEREBRAS and not api_key:
        raise ValueError("Cerebras の API キーを入力してください。")
    elif provider == ApiProvider.SAKURA and not api_key:
        raise ValueError("Sakura の API キーを入力してください。")
    elif provider == ApiProvider.CUSTOM:
        if not endpoint:
            raise ValueError("APIエンドポイントを入力してください。")
        if not api_key:
            raise ValueError("API キーを入力してください。")


def call_translation_api(
    config: AppConfig,
    source_text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """同期的に翻訳 API を呼び出し、翻訳結果文字列を返す."""
    system_content = expand_template(
        config.system_prompt,
        source_language=source_lang,
        target_language=target_lang,
    )
    user_content = expand_template(
        config.user_message_template,
        source_language=source_lang,
        target_language=target_lang,
        input_text=source_text,
    )

    endpoint, model, api_key = _resolve_api_settings(config)
    _validate_api_settings(config, endpoint, model, api_key)

    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    if model:
        payload["model"] = model

    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.debug("POST %s  payload=%s", endpoint, payload)

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=config.timeout)
    resp.raise_for_status()

    data: dict[str, Any] = resp.json()
    choices = data.get("choices")
    if not choices:
        raise ValueError("API response contains no choices")

    message = choices[0].get("message", {})
    return str(message.get("content", "")).strip()


# ------------------------------------------------------------------
# Google Translate 非公式 API
# ------------------------------------------------------------------

_GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"


def call_google_translate(
    source_text: str,
    source_lang: str,
    target_lang: str,
    timeout: int = 60,
) -> str:
    """Google Translate 非公式 API でテキストを翻訳する.

    translate.googleapis.com の無料エンドポイントを使用。
    API キー不要だがレートリミットの可能性あり。
    """
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": source_text,
    }
    logger.debug("GET %s  params=%s", _GOOGLE_TRANSLATE_URL, params)

    resp = requests.get(_GOOGLE_TRANSLATE_URL, params=params, timeout=timeout)
    resp.raise_for_status()

    data: list[Any] = resp.json()
    segments = data[0]
    if not segments:
        raise ValueError("Google Translate returned empty response")

    return "".join(str(seg[0]) for seg in segments if seg and seg[0])


# ------------------------------------------------------------------
# プロバイダー振り分け
# ------------------------------------------------------------------

def translate_text(
    config: AppConfig,
    source_text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """設定に応じて適切な翻訳 API を呼び出す."""
    if config.provider == ApiProvider.GOOGLE:
        return call_google_translate(
            source_text, source_lang, target_lang, config.timeout,
        )
    return call_translation_api(config, source_text, source_lang, target_lang)


# ------------------------------------------------------------------
# QThread ワーカー
# ------------------------------------------------------------------

class _TranslationWorker(QObject):
    finished = pyqtSignal(str, float)
    error = pyqtSignal(str)

    def __init__(
        self,
        config: AppConfig,
        source_text: str,
        source_lang: str,
        target_lang: str,
    ) -> None:
        super().__init__()
        self._config = config
        self._source_text = source_text
        self._source_lang = source_lang
        self._target_lang = target_lang

    def run(self) -> None:
        start = time.perf_counter()
        try:
            result = translate_text(
                self._config,
                self._source_text,
                self._source_lang,
                self._target_lang,
            )
            elapsed = time.perf_counter() - start
            self.finished.emit(result, elapsed)
        except requests.ConnectionError:
            self.error.emit("接続エラー: API サーバーに接続できません。URL を確認してください。")
        except requests.Timeout:
            self.error.emit("タイムアウト: API サーバーが応答しません。")
        except requests.HTTPError as exc:
            self.error.emit(f"HTTP エラー: {exc.response.status_code} — {exc.response.text[:200]}")
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"エラー: {exc}")


class TranslationManager(QObject):
    """メインウィンドウから利用する翻訳マネージャー.

    翻訳リクエストごとに QThread を生成・管理する。
    """

    translation_finished = pyqtSignal(str, float)
    translation_error = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _TranslationWorker | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def translate(
        self,
        config: AppConfig,
        source_text: str,
        source_lang: str,
        target_lang: str,
    ) -> None:
        if self.is_running:
            return

        self._thread = QThread()
        self._worker = _TranslationWorker(config, source_text, source_lang, target_lang)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)

        self._thread.start()

    def _on_finished(self, result: str, elapsed: float) -> None:
        self.translation_finished.emit(result, elapsed)

    def _on_error(self, message: str) -> None:
        self.translation_error.emit(message)

    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
