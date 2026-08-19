"""Cerebras / Sakura の利用可能モデルを動的に解決する。"""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable
from dataclasses import dataclass

import requests

from src.config import ApiProvider

_MODEL_ENDPOINTS: dict[ApiProvider, str] = {
    ApiProvider.CEREBRAS: "https://api.cerebras.ai/v1/models",
    ApiProvider.SAKURA: "https://api.ai.sakura.ad.jp/v1/models",
}
_CACHE_TTL_SECONDS = 10 * 60
_NON_CHAT_PATTERN = re.compile(
    r"(?:^|[/_.-])(embedding|embed|whisper|speech|tts|voice|e5)(?:$|[/_.-])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    created: int


@dataclass(frozen=True)
class _CacheEntry:
    credential_fingerprint: str
    expires_at: float
    models: tuple[ModelInfo, ...]


_catalog_cache: dict[ApiProvider, _CacheEntry] = {}


def is_chat_model(model_id: str) -> bool:
    return _NON_CHAT_PATTERN.search(model_id) is None


def select_chat_model(provider: ApiProvider, models: list[ModelInfo]) -> str:
    candidates = [model for model in models if is_chat_model(model.model_id)]
    if not candidates:
        raise ValueError("利用可能なチャットモデルがモデル一覧にありません。")
    candidates.sort(
        key=lambda model: (
            _model_priority(provider, model.model_id),
            -model.created,
            model.model_id.casefold(),
        )
    )
    return candidates[0].model_id


def resolve_provider_model(
    provider: ApiProvider,
    api_key: str,
    configured_model: str,
    timeout: int,
    *,
    request_get: Callable[..., requests.Response] = requests.get,
) -> str:
    configured = configured_model.strip()
    try:
        models = _get_models(provider, api_key, timeout, request_get=request_get)
    except (requests.RequestException, ValueError) as error:
        if configured:
            return configured
        raise ValueError(
            f"{provider.value} のモデル一覧を取得できませんでした。APIキーと接続を確認してください。"
        ) from error

    available_ids = {model.model_id for model in models if is_chat_model(model.model_id)}
    if configured and configured in available_ids:
        return configured
    return select_chat_model(provider, list(models))


def _get_models(
    provider: ApiProvider,
    api_key: str,
    timeout: int,
    *,
    request_get: Callable[..., requests.Response],
) -> tuple[ModelInfo, ...]:
    endpoint = _MODEL_ENDPOINTS.get(provider)
    if endpoint is None:
        raise ValueError(f"モデル一覧の自動取得に対応していません: {provider.value}")

    fingerprint = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    now = time.monotonic()
    cached = _catalog_cache.get(provider)
    if (
        cached is not None
        and cached.credential_fingerprint == fingerprint
        and cached.expires_at > now
    ):
        return cached.models

    response = request_get(
        endpoint,
        headers={"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
        timeout=min(timeout, 15),
    )
    response.raise_for_status()
    models = _parse_catalog(response.json())
    _catalog_cache[provider] = _CacheEntry(
        credential_fingerprint=fingerprint,
        expires_at=now + _CACHE_TTL_SECONDS,
        models=models,
    )
    return models


def _parse_catalog(payload: object) -> tuple[ModelInfo, ...]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("モデル一覧の応答形式が不正です。")
    models: list[ModelInfo] = []
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue
        created = item.get("created")
        models.append(
            ModelInfo(
                model_id=model_id.strip(),
                created=int(created) if isinstance(created, int | float) else 0,
            )
        )
    if not models:
        raise ValueError("モデル一覧が空です。")
    return tuple(models)


def _model_priority(provider: ApiProvider, model_id: str) -> int:
    lowered = model_id.casefold()
    if provider == ApiProvider.SAKURA:
        if any(name in lowered for name in ("llm-jp", "plamo", "cotomi")):
            return 0
        if lowered == "gpt-oss-120b":
            return 1
    elif provider == ApiProvider.CEREBRAS and lowered == "gpt-oss-120b":
        return 0
    if any(name in lowered for name in ("coder", "code")):
        return 4
    if re.search(r"(?:^|[/_.-])(?:vl|vision)(?:$|[/_.-])", lowered):
        return 3
    return 2


def clear_model_catalog_cache() -> None:
    """テストと明示更新用にプロセス内キャッシュを破棄する。"""

    _catalog_cache.clear()
