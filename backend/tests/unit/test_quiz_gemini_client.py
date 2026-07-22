import unittest
from unittest.mock import patch, MagicMock
import json
import os
import ast
import urllib.error

from app.infrastructure.adapters.quiz_gemini_client import (
    call_gemini_sync,
    call_gemini_api,
)


class TestQuizGeminiClient(unittest.IsolatedAsyncioTestCase):

    @patch("urllib.request.urlopen")
    def test_valid_response_returns_text(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": '[{"question": "Q1"}]'}]
                }
            }]
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = call_gemini_sync("fake_key", {"test": "payload"})
        self.assertEqual(res, '[{"question": "Q1"}]')

    @patch("urllib.request.urlopen")
    def test_response_without_candidates_returns_fallback(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"candidates": []}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = call_gemini_sync("fake_key", {"test": "payload"})
        self.assertEqual(res, "{}")

    @patch("urllib.request.urlopen")
    def test_response_without_parts_returns_fallback(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": []}}]
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = call_gemini_sync("fake_key", {"test": "payload"})
        self.assertEqual(res, "{}")

    @patch("urllib.request.urlopen")
    def test_network_or_http_error_returns_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Network Error")
        res = call_gemini_sync("fake_key", {"test": "payload"})
        self.assertEqual(res, "{}")

    @patch("urllib.request.urlopen")
    def test_invalid_json_returns_fallback(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json text"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = call_gemini_sync("fake_key", {"test": "payload"})
        self.assertEqual(res, "{}")

    @patch("urllib.request.urlopen")
    def test_uses_gemini_2_5_flash_model(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "OK"}]}}]
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        call_gemini_sync("my_secret_key", {"test": "payload"})
        req = mock_urlopen.call_args[0][0]
        self.assertIn("gemini-2.5-flash:generateContent", req.full_url)
        self.assertIn("key=my_secret_key", req.full_url)

    @patch("app.infrastructure.adapters.quiz_gemini_client.call_gemini_sync")
    async def test_async_call_delegates_to_sync_via_thread(self, mock_sync):
        mock_sync.return_value = '[{"question": "Q1"}]'
        res = await call_gemini_api("key_123", {"payload": True})
        self.assertEqual(res, '[{"question": "Q1"}]')
        mock_sync.assert_called_once_with("key_123", {"payload": True})

    def test_quiz_endpoint_imports_client_from_infrastructure(self):
        quiz_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/infrastructure/api/v1/endpoints/quiz.py"
        )
        with open(quiz_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("from app.infrastructure.adapters.quiz_gemini_client import call_gemini_api", content)
        self.assertNotIn("urllib.request.urlopen", content)
        self.assertNotIn("def call_gemini_sync", content)

    def test_chat_service_remains_deleted(self):
        legacy_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/chat_service.py"
        )
        self.assertFalse(os.path.exists(legacy_path), "chat_service.py must remain deleted")

    def test_application_layer_purity(self):
        app_dir = os.path.join(os.path.dirname(__file__), "../../app/application")
        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure"]
        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    parsed = ast.parse(code)
                    imported_modules = []
                    for node in ast.walk(parsed):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.append(node.module)

                    for mod in imported_modules:
                        for prefix in forbidden_prefixes:
                            self.assertFalse(
                                mod.startswith(prefix),
                                f"Forbidden import '{mod}' found in {filepath}"
                            )

    def test_quiz_endpoint_module_import_success(self):
        import importlib
        mod = importlib.import_module("app.infrastructure.api.v1.endpoints.quiz")
        self.assertTrue(hasattr(mod, "generate_quiz"))


if __name__ == "__main__":
    unittest.main()
