"""Gemini interpretation adapter with validation and deterministic fallback."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any


OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["summary", "cardInterpretations", "relationships", "advice", "reflectionQuestion", "disclaimerCode"],
    "properties": {
        "summary": {"type": "string"},
        "cardInterpretations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["positionId", "cardId", "interpretation", "evidence"],
                "properties": {
                    "positionId": {"type": "string"},
                    "cardId": {"type": "string"},
                    "interpretation": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "relationships": {"type": "array", "items": {"type": "object"}},
        "advice": {"type": "array", "items": {"type": "string"}},
        "reflectionQuestion": {"type": "string"},
        "disclaimerCode": {"type": ["string", "null"]},
    },
}


def _valid_response(value: Any, known_card_ids: set[str] | None = None) -> bool:
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("summary"), str) or not isinstance(value.get("cardInterpretations"), list):
        return False
    if not isinstance(value.get("relationships"), list) or not isinstance(value.get("advice"), list):
        return False
    if not isinstance(value.get("reflectionQuestion"), str):
        return False
    if value.get("disclaimerCode") is not None and not isinstance(value.get("disclaimerCode"), str):
        return False
    return all(
        isinstance(item, dict)
        and isinstance(item.get("positionId"), str)
        and isinstance(item.get("cardId"), str)
        and isinstance(item.get("interpretation"), str)
        and isinstance(item.get("evidence"), list)
        and (known_card_ids is None or item.get("cardId") in known_card_ids)
        and all(isinstance(evidence, str) for evidence in item["evidence"])
        for item in value["cardInterpretations"]
    )


def _generate_json(client: Any, prompt: str, schema: dict[str, Any], model: str, max_output_tokens: int) -> Any:
    """Support test doubles and small adapters that predate the token-limit argument."""

    try:
        return client.generate_json(prompt, schema, model, max_output_tokens)
    except TypeError:
        return client.generate_json(prompt, schema, model)


class GeminiInterpreter:
    def __init__(self, client: Any, model: str | None = None, max_retries: int | None = None, timeout_seconds: float | None = None, max_output_tokens: int | None = None):
        self.client = client
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "2")) if max_retries is None else max_retries
        self.timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "15")) if timeout_seconds is None else timeout_seconds
        self.max_output_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "800")) if max_output_tokens is None else max_output_tokens

    def _prompt(self, request: dict[str, Any]) -> str:
        return (
            "あなたは内省を支援するカード解釈者です。断定や専門判断を避け、相談者が自分で判断できる具体的な小さな行動を提案してください。"
            "次のJSONだけを返してください。\n"
            f"質問: {request['question']}\nカード: {request['draws']}\n"
            "医療・法律・金融・生死について予言や断定をしないでください。"
        )

    def _fallback(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": "問いを一文に絞り、すでに得た情報を整理してから次の一歩を選びます。",
            "cardInterpretations": [
                {
                    "positionId": draw.get("positionId", "guidance"),
                    "cardId": draw.get("cardId", "unknown"),
                    "interpretation": "カードの象徴を、相談内容を見直すための問いとして扱います。",
                    "evidence": ["内省", "選別"],
                }
                for draw in request["draws"]
            ],
            "relationships": [],
            "advice": ["事実・推測・希望を分けて一つずつ書き出す"],
            "reflectionQuestion": "いま確かめられる事実は何ですか？",
            "disclaimerCode": "reflective-not-professional-advice",
            "fallbackUsed": True,
        }

    def interpret(self, request: dict[str, Any], known_card_ids: set[str] | None = None) -> dict[str, Any]:
        question = request.get("question", "")
        draws = request.get("draws", [])
        if not isinstance(question, str) or len(question) > 1000:
            raise ValueError("question must be a string of at most 1000 characters")
        if not isinstance(draws, list) or not 1 <= len(draws) <= 3:
            raise ValueError("draws must contain between one and three cards")
        if any(
            not isinstance(draw, dict)
            or not isinstance(draw.get("cardId"), str)
            or not isinstance(draw.get("positionId"), str)
            or draw.get("orientation") not in {"upright", "reversed"}
            for draw in draws
        ):
            raise ValueError("each draw must contain cardId, positionId, and a valid orientation")
        if known_card_ids is not None and any(draw.get("cardId") not in known_card_ids for draw in draws):
            raise ValueError("request contains an unknown card")
        prompt = self._prompt(request)
        for attempt in range(self.max_retries + 1):
            executor = ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(_generate_json, self.client, prompt, OUTPUT_SCHEMA, self.model, self.max_output_tokens)
                value = future.result(timeout=self.timeout_seconds)
                if _valid_response(value, known_card_ids):
                    return {**value, "fallbackUsed": False}
            except Exception:
                if attempt < self.max_retries:
                    time.sleep(min(0.25 * (attempt + 1), 1.0))
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        return self._fallback(request)


class GoogleGenaiClient:
    """Lazy wrapper so unit tests do not require the optional Google SDK."""

    def __init__(self, api_key: str | None = None):
        from google import genai

        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])

    def generate_json(self, prompt: str, schema: dict[str, Any], model: str, max_output_tokens: int = 800) -> dict[str, Any]:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": schema, "max_output_tokens": max_output_tokens},
        )
        import json

        return json.loads(response.text)
