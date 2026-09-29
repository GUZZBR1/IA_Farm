import os
import sys
import types
import unittest
from unittest.mock import patch

from tools.orchastrator import LLM_UNAVAILABLE_RESPONSE, Orchestrator


class FakeDatabase:
    def query(self, query, k=5, filters=None):
        return []


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class LlmContractTests(unittest.TestCase):
    def test_missing_fallback_key_fails_closed(self):
        requests = types.SimpleNamespace(
            post=lambda *args, **kwargs: FakeResponse(503, {})
        )
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {"requests": requests}):
            response = Orchestrator(db=FakeDatabase())._call_llm("test")
        self.assertEqual(response, LLM_UNAVAILABLE_RESPONSE)

    def test_openrouter_fallback_uses_environment_key(self):
        calls = []

        def post(url, **kwargs):
            calls.append((url, kwargs))
            if "11434" in url:
                return FakeResponse(503, {})
            return FakeResponse(200, {"choices": [{"message": {"content": "fallback ok"}}]})

        requests = types.SimpleNamespace(post=post)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-key"}), patch.dict(
            sys.modules, {"requests": requests}
        ):
            response = Orchestrator(db=FakeDatabase())._call_llm("test")

        self.assertEqual(response, "fallback ok")
        self.assertEqual(calls[1][1]["headers"]["Authorization"], "Bearer test-only-key")


if __name__ == "__main__":
    unittest.main()
