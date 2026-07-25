"""Offline quality checks and release-manifest generation for public content."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    return re.sub(r"[^\w]+", "", value.casefold())


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[\w]+", value.casefold()) if len(token) > 1}


def similarity_report(items: list[dict[str, Any]], threshold: float = 0.35) -> list[dict[str, Any]]:
    """Return review-only Jaccard similarity pairs; never auto-reject a card."""

    pairs: list[dict[str, Any]] = []
    for index, left in enumerate(items):
        left_id = left.get("id") or left.get("name", "")
        left_text = " ".join(str(left.get(key, "")) for key in ("name", "subtitle", "centralParadox", "uprightCore", "reversedCore", "lore"))
        left_tokens = _tokens(left_text)
        for right in items[index + 1 :]:
            right_id = right.get("id") or right.get("name", "")
            right_text = " ".join(str(right.get(key, "")) for key in ("name", "subtitle", "centralParadox", "uprightCore", "reversedCore", "lore"))
            right_tokens = _tokens(right_text)
            union = left_tokens | right_tokens
            score = len(left_tokens & right_tokens) / len(union) if union else 0.0
            if score >= threshold:
                pairs.append({"left": left_id, "right": right_id, "jaccard": round(score, 4), "reviewRequired": True})
    return sorted(pairs, key=lambda item: item["jaccard"], reverse=True)


def build_quality_report(content_root: Path, repository_root: Path, batch_path: Path | None = None) -> dict[str, Any]:
    content_root = Path(content_root)
    repository_root = Path(repository_root)
    manifest = read_json(content_root / "manifest.json")
    cards = [read_json(content_root / path) for path in manifest["files"]["cards"]]
    archetypes = {item["id"]: item for item in (read_json(content_root / path) for path in manifest["files"]["archetypes"])}
    catalog = read_json(content_root / manifest["files"]["assetCatalog"])
    errors: list[str] = []
    warnings: list[str] = []
    seen_names: dict[str, str] = {}
    for card in cards:
        archetype = archetypes.get(card["archetypeId"])
        if archetype is None:
            errors.append(f"{card['id']}: unknown archetype")
            continue
        required = set(archetype["semanticAnchors"]["requiredThemeIds"])
        inherited = set(card["inheritedThemeIds"])
        if len(required & inherited) < archetype["inheritancePolicy"]["minimumRequiredThemeMatches"]:
            errors.append(f"{card['id']}: insufficient inherited themes")
        name = next(iter(card["name"].values()))
        key = normalize(name)
        if key in seen_names:
            warnings.append(f"duplicate normalized card name: {card['id']} and {seen_names[key]}")
        else:
            seen_names[key] = card["id"]
    roots = {root["id"]: root for root in catalog["assetRoots"]}
    for asset in catalog["assets"]:
        for variant in asset["variants"]:
            if asset["status"] != "available" or variant["source"]["type"] != "local":
                continue
            file_path = repository_root / roots[variant["source"]["rootId"]]["basePath"] / variant["source"]["path"]
            if not file_path.is_file():
                errors.append(f"{asset['id']}: missing local asset {file_path}")
                continue
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if variant.get("sha256") and variant["sha256"] != digest:
                errors.append(f"{asset['id']}: SHA-256 mismatch")
    similarity_pairs: list[dict[str, Any]] = []
    if batch_path:
        batch = read_json(Path(batch_path))
        batch_names: set[str] = set()
        for item in batch.get("cards", []):
            key = normalize(item.get("name", ""))
            if key in batch_names:
                warnings.append(f"duplicate batch name: {item.get('name', '')}")
            batch_names.add(key)
        similarity_pairs = similarity_report(batch.get("cards", []))
    return {"summary": {"cards": len(cards), "archetypes": len(archetypes), "errors": len(errors), "warnings": len(warnings), "similarityPairs": len(similarity_pairs)}, "errors": errors, "warnings": warnings, "similarityPairs": similarity_pairs, "review": {"status": "needs-review" if batch_path else "not-applicable", "humanApprovalRequiredForPublished": True}}


def build_release_manifest(content_root: Path, repository_root: Path) -> dict[str, Any]:
    content_root = Path(content_root)
    repository_root = Path(repository_root)
    source = read_json(content_root / "manifest.json")
    relative_files = [path for key, paths in source["files"].items() if key != "assetCatalog" for path in paths]
    relative_files.append(source["files"]["assetCatalog"])
    files = []
    for relative in relative_files:
        file_path = content_root / relative
        files.append({"path": relative, "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()})
    return {"releaseId": source["releaseId"], "schemaVersion": source["schemaVersion"], "releasedAt": datetime.now(timezone.utc).isoformat(), "minimumAppVersion": source["minimumAppVersion"], "counts": source["counts"], "files": files}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-root", default="packages/content")
    parser.add_argument("--output", default="artifacts/content-quality-report.json")
    parser.add_argument("--release-output", default="artifacts/release-manifest.json")
    parser.add_argument("--batch")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_quality_report(root / args.content_root, root, Path(args.batch) if args.batch else None)
    release = build_release_manifest(root / args.content_root, root)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release_output = root / args.release_output
    release_output.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Quality report: {report['summary']['errors']} errors, {report['summary']['warnings']} warnings")
    print(f"Release manifest: {release_output}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
