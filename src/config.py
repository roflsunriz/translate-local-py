"""設定管理 — JSON 永続化とデフォルト値."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

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
    api_url: str = "http://127.0.0.1:8080"
    model: str = ""
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

        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return cls(**filtered)
