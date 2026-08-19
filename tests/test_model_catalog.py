from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests

from src.config import ApiProvider
from src.model_catalog import (
    ModelInfo,
    clear_model_catalog_cache,
    resolve_provider_model,
    select_chat_model,
)


class ModelCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_model_catalog_cache()

    def test_sakura_selection_excludes_non_chat_and_ignores_order(self) -> None:
        models = [
            ModelInfo("preview/Qwen3-Embedding-4B-FP16", 40),
            ModelInfo("preview/Kimi-K2.7-Code", 30),
            ModelInfo("gpt-oss-120b", 20),
            ModelInfo("llm-jp-3.1-8x13b-instruct4", 10),
        ]
        expected = "llm-jp-3.1-8x13b-instruct4"
        self.assertEqual(select_chat_model(ApiProvider.SAKURA, models), expected)
        self.assertEqual(select_chat_model(ApiProvider.SAKURA, list(reversed(models))), expected)

    def test_removed_configured_model_is_replaced_from_authenticated_catalog(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "object": "list",
            "data": [
                {"id": "whisper-large-v3-turbo", "created": 30},
                {"id": "new-chat-model", "created": 20},
            ],
        }
        request_get = Mock(return_value=response)

        selected = resolve_provider_model(
            ApiProvider.CEREBRAS,
            "test-key",
            "removed-model",
            60,
            request_get=request_get,
        )

        self.assertEqual(selected, "new-chat-model")
        self.assertEqual(
            request_get.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )

    def test_catalog_failure_uses_existing_model_temporarily(self) -> None:
        request_get = Mock(side_effect=requests.ConnectionError("offline"))
        selected = resolve_provider_model(
            ApiProvider.CEREBRAS,
            "test-key",
            "existing-model",
            60,
            request_get=request_get,
        )
        self.assertEqual(selected, "existing-model")


if __name__ == "__main__":
    unittest.main()
