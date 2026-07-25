"""Generate and validate offline card candidates through a Gemini-compatible client."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


CANDIDATE_SCHEMA = {
    "type": "object",
    "required": ["cards"],
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "subtitle", "manifestationForm", "centralParadox", "uprightCore", "reversedCore"],
                "properties": {
                    "name": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "manifestationForm": {"type": "string"},
                    "centralParadox": {"type": "string"},
                    "uprightCore": {"type": "string"},
                    "reversedCore": {"type": "string"},
                },
            },
        }
    },
}
HIGH_RISK_TERMS = ("必ず", "絶対", "運命として決ま", "治る", "診断", "投資すべき", "死ぬ")


def load_batch(path: Path) -> dict[str, Any]:
    batch = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"schemaVersion", "id", "targetArchetypeId", "requestedCount", "requiredVariationAxes", "avoidTerms", "outputLocale"}
    missing = required - batch.keys()
    if missing:
        raise ValueError(f"batch is missing fields: {', '.join(sorted(missing))}")
    if batch["schemaVersion"] != "1.0.0" or batch["outputLocale"] != "ja-JP":
        raise ValueError("unsupported batch schema or locale")
    return batch


def candidate_prompt(batch: dict[str, Any], archetype: dict[str, Any], existing_names: list[str]) -> str:
    themes = ", ".join(archetype.get("semanticAnchors", {}).get("requiredThemeIds", []))
    avoid = ", ".join(batch.get("avoidTerms", []))
    variation = ", ".join(batch.get("requiredVariationAxes", []))
    return (
        "カード候補をJSONだけで生成してください。未来・健康・法律・金融の断定や恐怖喚起を避け、"
        "原型の意味を継承しつつ既存名を言い換えないでください。\n"
        f"対象原型: {batch['targetArchetypeId']} / 必須テーマ: {themes}\n"
        f"必要数: {batch['requestedCount']} / 変化軸: {variation}\n"
        f"避ける語: {avoid}\n既存名: {', '.join(existing_names)}\n"
        "各候補は name, subtitle, manifestationForm, centralParadox, uprightCore, reversedCore を持ちます。"
    )


def validate_candidates(value: Any, batch: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("cards"), list):
        raise ValueError("candidate response must contain cards array")
    cards = value["cards"]
    if len(cards) != batch["requestedCount"]:
        raise ValueError(f"expected {batch['requestedCount']} candidates, got {len(cards)}")
    names: set[str] = set()
    avoid_terms = [term.casefold() for term in batch.get("avoidTerms", [])]
    for card in cards:
        if not isinstance(card, dict) or not all(isinstance(card.get(key), str) and card[key].strip() for key in CANDIDATE_SCHEMA["properties"]["cards"]["items"]["required"]):
            raise ValueError("candidate is missing a required non-empty field")
        candidate_text = " ".join(str(card[key]) for key in CANDIDATE_SCHEMA["properties"]["cards"]["items"]["required"]).casefold()
        name = card["name"].casefold()
        if name in names:
            raise ValueError(f"duplicate candidate name: {card['name']}")
        if any(term in candidate_text for term in avoid_terms):
            raise ValueError(f"candidate contains avoid term: {card['name']}")
        if any(term in candidate_text for term in HIGH_RISK_TERMS):
            raise ValueError(f"candidate contains high-risk deterministic wording: {card['name']}")
        names.add(name)
    return {"schemaVersion": "1.0.0", "batchId": batch["id"], "status": "automatically-validated", "cards": cards}


def generate_candidates(
    client: Any,
    batch: dict[str, Any],
    archetype: dict[str, Any],
    existing_names: list[str],
    model: str | None = None,
    max_retries: int | None = None,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    if archetype.get("id") and archetype["id"] != batch["targetArchetypeId"]:
        raise ValueError("batch target archetype does not match archetype input")
    prompt = candidate_prompt(batch, archetype, existing_names)
    cache_path = Path(cache_path) if cache_path else None
    cache_key = hashlib.sha256(f"{model or os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')}\n{prompt}".encode("utf-8")).hexdigest()
    if cache_path and cache_path.is_file():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("cacheKey") == cache_key:
            return validate_candidates(cached["response"], batch)
    retries = int(os.getenv("GEMINI_MAX_RETRIES", "2")) if max_retries is None else max_retries
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.generate_json(prompt, CANDIDATE_SCHEMA, model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"))
            result = validate_candidates(response, batch)
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps({"cacheKey": cache_key, "response": response}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return result
        except Exception as error:
            last_error = error
            if attempt < retries:
                continue
    raise ValueError(f"candidate generation failed after {retries + 1} attempts: {last_error}") from last_error


class GoogleGenaiCandidateClient:
    def __init__(self, api_key: str | None = None):
        from google import genai

        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])

    def generate_json(self, prompt: str, schema: dict[str, Any], model: str) -> dict[str, Any]:
        response = self._client.models.generate_content(model=model, contents=prompt, config={"response_mime_type": "application/json", "response_schema": schema})
        return json.loads(response.text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--archetype", required=True, help="JSON file for the target archetype")
    parser.add_argument("--existing-names", nargs="*", default=[])
    parser.add_argument("--output", required=True)
    parser.add_argument("--cache")
    args = parser.parse_args()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY is required for candidate generation; use the quality CLI for offline validation")
    result = generate_candidates(GoogleGenaiCandidateClient(), load_batch(Path(args.batch)), json.loads(Path(args.archetype).read_text(encoding="utf-8")), args.existing_names, cache_path=Path(args.cache) if args.cache else None)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(result['cards'])} candidates with status={result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
