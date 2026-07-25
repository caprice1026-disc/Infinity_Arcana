import unittest

from apps.api.interpreter import GeminiInterpreter


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def generate_json(self, prompt, schema, model):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class InterpretationTests(unittest.TestCase):
    request = {"question": "今週の仕事で意識することは？", "locale": "ja-JP", "draws": [{"cardId": "babel-library", "orientation": "upright", "positionId": "guidance"}]}
    valid_response = {
        "summary": "問いを一文に絞る",
        "cardInterpretations": [{"positionId": "guidance", "cardId": "babel-library", "interpretation": "終了条件を定める", "evidence": ["探求"]}],
        "relationships": [],
        "advice": ["終了条件を決める"],
        "reflectionQuestion": "何を知れば決められますか？",
        "disclaimerCode": "reflective-not-professional-advice",
    }

    def test_valid_structured_response_is_returned(self):
        client = FakeClient(self.valid_response)
        result = GeminiInterpreter(client=client, model="test-model").interpret(self.request)
        self.assertFalse(result["fallbackUsed"])
        self.assertEqual(result["advice"], ["終了条件を決める"])
        self.assertEqual(client.calls, 1)

    def test_invalid_response_and_api_error_fall_back_without_raising(self):
        client = FakeClient({"summary": "missing fields"})
        result = GeminiInterpreter(client=client, model="test-model").interpret(self.request)
        self.assertTrue(result["fallbackUsed"])
        self.assertTrue(result["summary"])

        failing = FakeClient(error=RuntimeError("429 RESOURCE_EXHAUSTED"))
        fallback = GeminiInterpreter(client=failing, model="test-model", max_retries=1).interpret(self.request)
        self.assertTrue(fallback["fallbackUsed"])
        self.assertEqual(failing.calls, 2)

    def test_unknown_card_is_rejected_before_client_call(self):
        client = FakeClient({})
        with self.assertRaises(ValueError):
            GeminiInterpreter(client=client, model="test-model").interpret({**self.request, "draws": [{"cardId": "unknown"}]}, {"babel-library"})
        self.assertEqual(client.calls, 0)
