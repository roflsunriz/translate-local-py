"""設定管理 - JSON 永続化とデフォルト値."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _runtime_root() -> Path:
    """Frozen app は exe の配置先、通常実行はリポジトリルートを返す."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _PROJECT_ROOT


def _runtime_resource_root() -> Path:
    """PyInstaller の onefile 展開先も含めたリソースルートを返す."""

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return _PROJECT_ROOT


_CONFIG_PATH = _runtime_root() / "config.json"
RESOURCES_DIR = _runtime_resource_root() / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"


class ApiProvider(Enum):
    LOCAL = "local"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    CEREBRAS = "cerebras"
    SAKURA = "sakura"
    CUSTOM = "custom"


PROVIDER_LABELS: dict[ApiProvider, str] = {
    ApiProvider.LOCAL: "ローカル",
    ApiProvider.GOOGLE: "Google翻訳",
    ApiProvider.OPENROUTER: "OpenRouter",
    ApiProvider.CEREBRAS: "Cerebras",
    ApiProvider.SAKURA: "Sakura",
    ApiProvider.CUSTOM: "自由入力",
}

PROVIDER_ORDER: list[ApiProvider] = [
    ApiProvider.LOCAL,
    ApiProvider.GOOGLE,
    ApiProvider.OPENROUTER,
    ApiProvider.CEREBRAS,
    ApiProvider.SAKURA,
    ApiProvider.CUSTOM,
]

CEREBRAS_MODELS: list[str] = [
    "llama3.1-8b",
    "gpt-oss-120b",
    "qwen-3-235b-a22b-instruct-2507",
    "zai-glm-4.7",
]

SAKURA_MODELS: list[str] = [
    "Qwen3-Coder-30B-A3B-Instruct",
    "Qwen3-Coder-480B-A35B-Instruct-FP8",
    "gpt-oss-120b",
    "llm-jp-3.1-8x13b-instruct4",
    "preview/Phi-4-mini-instruct-cpu",
    "preview/Phi-4-multimodal-instruct",
    "preview/Qwen3-0.6B-cpu",
    "preview/Qwen3-VL-30B-A3B-Instruct",
]

DEFAULT_SYSTEM_PROMPT = (
    "あなたはプロフェッショナルの高度な翻訳エンジンである。"
    "あなたの役割は、原文の書式、専門用語、略語を正確に保持しつつ、"
    "テキストを{{target_language}}に正確に翻訳することである。"
    "翻訳結果にはいかなる説明や注釈も付加してはならない。\n"
    "---\n"
    "翻訳結果の文末の敬体表現「～ます。～です。～ました。」を禁止する。"
    "如何なる時も常体表現「～だ。～である。～した。」で翻訳せよ。"
    "具体例は次の通り。\n"
    "原文例1: Running is good constitution to your health.\n"
    "翻訳文例1: ランニングは健康に良い体質を作る。\n"
    "原文例2: Here is an apple on the table. "
    "It's smell is freshly, sweet, and ready to eat. \n"
    "翻訳文例2: テーブルの上にリンゴが置いてある。"
    "その香りは新鮮で甘く、食べるのに丁度よい。\n"
    "原文例3: No need to mention, "
    "we have to hurry as possible as we can.\n"
    "翻訳文例3: 言うまでもなく、私たちは可能な限り急ぐ必要がある。"
)

DEFAULT_USER_MESSAGE_TEMPLATE = (
    "<|plamo:op|>dataset\n"
    "translation\n"
    "<|plamo:op|>input lang={{source_language}}\n"
    "{{input_text}}\n"
    "<|plamo:op|>output lang={{target_language}}"
)

PRESET_LANGUAGES: list[tuple[str, str]] = [
    ("日本語", "ja"),
    ("英語", "en"),
    ("中国語(簡体字)", "zh"),
    ("中国語(繁体字)", "zh-TW"),
    ("韓国語", "ko"),
    ("スペイン語", "es"),
    ("フランス語", "fr"),
    ("ドイツ語", "de"),
    ("ポルトガル語", "pt"),
    ("ロシア語", "ru"),
]


@dataclass
class AppConfig:
    api_provider: str = ApiProvider.LOCAL.value
    local_api_url: str = "http://127.0.0.1:8080"
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    cerebras_api_key: str = ""
    cerebras_model: str = CEREBRAS_MODELS[0]
    sakura_api_key: str = ""
    sakura_model: str = SAKURA_MODELS[0]
    custom_api_url: str = ""
    custom_api_key: str = ""
    custom_model: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout: int = 60
    source_lang: str = "ja"
    target_lang: str = "en"
    system_prompt: str = field(default_factory=lambda: DEFAULT_SYSTEM_PROMPT)
    user_message_template: str = field(
        default_factory=lambda: DEFAULT_USER_MESSAGE_TEMPLATE,
    )
    opacity: float = 1.0
    always_on_top: bool = False
    window_geometry: str = ""

    @property
    def provider(self) -> ApiProvider:
        try:
            return ApiProvider(self.api_provider)
        except ValueError:
            return ApiProvider.LOCAL

    def provider_label(self) -> str:
        return PROVIDER_LABELS.get(self.provider, "ローカル")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path | None = None) -> None:
        target = path or _CONFIG_PATH
        data = asdict(self)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Config saved to %s", target)

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        target = path or _CONFIG_PATH
        if not target.exists():
            cfg = cls()
            cfg.save(target)
            return cfg

        try:
            raw: dict[str, Any] = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to read config — using defaults", exc_info=True)
            return cls()

        raw = cls._migrate_legacy_fields(raw)

        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return cls(**filtered)

    @staticmethod
    def _migrate_legacy_fields(raw: dict[str, Any]) -> dict[str, Any]:
        migrated = dict(raw)

        legacy_provider = migrated.get("api_provider")
        if legacy_provider == "openai":
            migrated["api_provider"] = ApiProvider.LOCAL.value

        legacy_api_url = migrated.pop("api_url", None)
        if legacy_api_url and not migrated.get("local_api_url"):
            migrated["local_api_url"] = legacy_api_url

        legacy_model = migrated.pop("model", None)
        if legacy_model and not migrated.get("custom_model"):
            migrated["custom_model"] = legacy_model

        return migrated
