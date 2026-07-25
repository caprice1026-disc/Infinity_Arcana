"""Convert the shared Knowledge Arcana Vol. 1 card back and link its cards."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ASSET_ID = "card-knowledge-arcana-vol-1-back"
PACK_ID = "knowledge-arcana-vol-1"
OUTPUT_RELATIVE_PATH = Path("cards") / PACK_ID / "back.webp"
OUTPUT_WIDTH = 1024
OUTPUT_HEIGHT = 1536


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    return stream["width"], stream["height"]


def build_pack_card_back(repository_root: Path, source_path: Path | None = None) -> dict[str, int]:
    """Build the shared card-back asset and link cards in the Knowledge pack."""

    repository_root = Path(repository_root)
    source_path = source_path or repository_root / "cards" / "template" / "card-knowledge-arcana-vol-1-back-v1.png"
    if not source_path.is_file():
        raise FileNotFoundError(f"Card-back source PNG is missing: {source_path}")
    content_root = repository_root / "packages" / "content"
    catalog_path = content_root / "assets" / "assets.json"
    catalog = _read_json(catalog_path)
    roots = {root["id"]: root for root in catalog["assetRoots"]}
    root = roots["sites-public"]
    output_path = repository_root / root["basePath"] / OUTPUT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(source_path), "-frames:v", "1", "-vf", f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:flags=lanczos", "-c:v", "libwebp", "-quality", "90", str(output_path)],
        check=True,
    )
    if _dimensions(output_path) != (OUTPUT_WIDTH, OUTPUT_HEIGHT):
        raise ValueError(f"Generated card back has incorrect dimensions: {output_path}")
    contents = output_path.read_bytes()
    variant = {
        "id": "display-local",
        "usage": "display",
        "mimeType": "image/webp",
        "width": OUTPUT_WIDTH,
        "height": OUTPUT_HEIGHT,
        "source": {"type": "local", "rootId": root["id"], "path": OUTPUT_RELATIVE_PATH.as_posix()},
        "byteSize": len(contents),
        "sha256": hashlib.sha256(contents).hexdigest(),
    }
    asset = next((item for item in catalog["assets"] if item["id"] == ASSET_ID), None)
    if asset is None:
        catalog["assets"].append({"id": ASSET_ID, "contentVersion": 1, "status": "available", "kind": "card-back", "defaultVariantId": "display-local", "variants": [variant]})
        catalog["catalogVersion"] += 1
    elif asset["status"] != "available" or asset["variants"] != [variant]:
        asset.update({"contentVersion": asset["contentVersion"] + 1, "status": "available", "kind": "card-back", "defaultVariantId": "display-local", "variants": [variant]})
        catalog["catalogVersion"] += 1
    _write_json(catalog_path, catalog)

    linked_card_count = 0
    for card_path in sorted((content_root / "cards").glob("*.json")):
        card = _read_json(card_path)
        if PACK_ID not in card.get("packIds", []):
            continue
        if card["visual"].get("cardBackAssetId") != ASSET_ID:
            card["visual"]["cardBackAssetId"] = ASSET_ID
            if "contentVersion" in card:
                card["contentVersion"] += 1
            _write_json(card_path, card)
        linked_card_count += 1
    return {"linked_card_count": linked_card_count}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    result = build_pack_card_back(root)
    print(f"Converted shared card back and linked {result['linked_card_count']} Knowledge Arcana cards.")
