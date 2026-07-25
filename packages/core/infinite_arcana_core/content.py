"""Read versioned public content from the repository manifest."""

from dataclasses import dataclass
from datetime import datetime
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


def filter_cards(
    cards: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    domain_ids: set[str] | None = None,
    pack_ids: set[str] | None = None,
    statuses: set[str] | None = None,
    as_of: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Apply domain, pack, lifecycle, and publication-window filters before drawing."""

    moment = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else None
    result: list[dict[str, Any]] = []
    for card in cards:
        if domain_ids and not domain_ids.intersection(card.get("domainIds", [])):
            continue
        if pack_ids and not pack_ids.intersection(card.get("packIds", [])):
            continue
        if statuses and card.get("status") not in statuses:
            continue
        publication = card.get("publication", {})
        if moment and publication.get("publishedAt"):
            published_at = datetime.fromisoformat(publication["publishedAt"].replace("Z", "+00:00"))
            if published_at > moment:
                continue
        if moment and publication.get("retiredAt"):
            retired_at = datetime.fromisoformat(publication["retiredAt"].replace("Z", "+00:00"))
            if retired_at <= moment:
                continue
        result.append(card)
    return tuple(result)
