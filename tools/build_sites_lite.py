"""Build a self-contained static Sites-lite artifact from public content."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def build_sites_lite(repository_root: Path) -> Path:
    root = Path(repository_root)
    source_app = root / "apps" / "sites-lite"
    dist = source_app / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    for name in ("index.html", "styles.css"):
        shutil.copy2(source_app / name, dist / name)
    shutil.copytree(source_app / "src", dist / "src")
    content_out = dist / "content"
    shutil.copytree(root / "packages" / "content", content_out)
    assets_out = dist / "assets"
    shutil.copytree(source_app / "public" / "assets", assets_out)
    catalog_path = content_out / "assets" / "assets.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for asset_root in catalog["assetRoots"]:
        asset_root["basePath"] = "assets"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dist


if __name__ == "__main__":
    output = build_sites_lite(Path(__file__).resolve().parents[1])
    print(f"Built Sites-lite static artifact at {output}")
