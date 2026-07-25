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


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        if self.path != "/api/readings/interpret":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 32_000:
                raise ValueError("request body must be between 1 and 32000 bytes")
            request = json.loads(self.rfile.read(content_length))
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
