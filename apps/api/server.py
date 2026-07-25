"""Small standard-library HTTP adapter for the interpretation endpoint."""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from apps.api.interpreter import GeminiInterpreter, GoogleGenaiClient
from packages.core.infinite_arcana_core.content import load_content


ROOT = Path(__file__).resolve().parents[2]
CONTENT = load_content(ROOT / "packages" / "content")
KNOWN_CARD_IDS = {card["id"] for card in CONTENT.cards}
KNOWN_CARDS = {card["id"]: card for card in CONTENT.cards}


def canonicalize_draws(request: dict) -> dict:
    """Replace client-supplied card fields with the server's versioned content."""

    canonical = dict(request)
    draws = []
    for draw in request.get("draws", []):
        card = KNOWN_CARDS.get(draw.get("cardId")) if isinstance(draw, dict) else None
        if card is None:
            draws.append(draw)
            continue
        requested_version = draw.get("contentVersion")
        if requested_version is not None and requested_version != card["contentVersion"]:
            raise ValueError(f"card contentVersion mismatch for {card['id']}")
        locale = card.get("defaultLocale", "ja-JP")
        localized = card.get("localizedContent", {}).get(locale, {})
        meanings = localized.get("meanings", {}).get(draw.get("orientation"), {})
        draws.append({
            "positionId": draw.get("positionId"),
            "cardId": card["id"],
            "contentVersion": card["contentVersion"],
            "orientation": draw.get("orientation"),
            "name": card.get("name", {}).get(locale, card["id"]),
            "meaning": {"keywords": meanings.get("keywords", []), "core": meanings.get("core", ""), "advice": meanings.get("advice", "")},
        })
    canonical["draws"] = draws
    return canonical


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        if self.path != "/api/readings/interpret":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 32_000:
                raise ValueError("request body must be between 1 and 32000 bytes")
            parsed = json.loads(self.rfile.read(content_length))
            if not isinstance(parsed, dict):
                raise ValueError("request body must be a JSON object")
            request = canonicalize_draws(parsed)
            if os.getenv("GEMINI_API_KEY"):
                interpreter = GeminiInterpreter(
                    client=GoogleGenaiClient(),
                    model=os.getenv("GEMINI_MODEL"),
                )
            else:
                interpreter = GeminiInterpreter(client=_FallbackClient())
            result = interpreter.interpret(request, KNOWN_CARD_IDS)
            payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_error(400, str(error))


class _FallbackClient:
    def generate_json(self, prompt, schema, model):
        raise RuntimeError("GEMINI_API_KEY is not configured")


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(os.getenv("PORT", "8000"))), Handler).serve_forever()
