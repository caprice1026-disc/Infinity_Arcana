"""Read versioned public content from the repository manifest."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ContentBundle:
    manifest: dict[str, Any]
    archetypes: tuple[dict[str, Any], ...]
    cards: tuple[dict[str, Any], ...]
    domains: tuple[dict[str, Any], ...]
    packs: tuple[dict[str, Any], ...]
    spreads: dict[str, dict[str, Any]]
    assets: dict[str, dict[str, Any]]


def _read(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def load_content(content_root: Path) -> ContentBundle:
    content_root = Path(content_root)
    manifest = _read(content_root, "manifest.json")
    files = manifest["files"]
    archetypes = tuple(_read(content_root, path) for path in files["archetypes"])
    cards = tuple(_read(content_root, path) for path in files["cards"])
    domains = tuple(_read(content_root, path) for path in files["domains"])
    packs = tuple(_read(content_root, path) for path in files["packs"])
    spreads = {item["id"]: item for item in (_read(content_root, path) for path in files.get("spreads", []))}
    assets_catalog = _read(content_root, files["assetCatalog"])
    assets = {item["id"]: item for item in assets_catalog["assets"]}
    return ContentBundle(manifest, archetypes, cards, domains, packs, spreads, assets)
