import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.content_pipeline.build_pack_card_back import build_pack_card_back


class PackCardBackTests(unittest.TestCase):
    def test_converts_back_and_links_every_card_to_the_shared_asset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "cards" / "template" / "card-knowledge-arcana-vol-1-back-v1.png"
            source.parent.mkdir(parents=True)
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=4x6", "-frames:v", "1", str(source)],
                check=True,
                capture_output=True,
            )
            content = root / "packages" / "content"
            (content / "assets").mkdir(parents=True)
            (content / "cards").mkdir()
            catalog_path = content / "assets" / "assets.json"
            catalog_path.write_text(
                json.dumps({"schemaVersion": "1.0.0", "catalogVersion": 1, "assetRoots": [{"id": "sites-public", "basePath": "apps/sites-lite/public/assets"}], "assets": []}),
                encoding="utf-8",
            )
            for card_id in ("first", "second"):
                (content / "cards" / f"{card_id}.json").write_text(
                    json.dumps({"id": card_id, "packIds": ["knowledge-arcana-vol-1"], "visual": {"cardBackAssetId": None}}), encoding="utf-8"
                )

            result = build_pack_card_back(root, source)

            output = root / "apps" / "sites-lite" / "public" / "assets" / "cards" / "knowledge-arcana-vol-1" / "back.webp"
            self.assertEqual(result["linked_card_count"], 2)
            self.assertTrue(output.exists())
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            asset = catalog["assets"][0]
            self.assertEqual(asset["id"], "card-knowledge-arcana-vol-1-back")
            self.assertEqual(asset["status"], "available")
            self.assertEqual(asset["variants"][0]["byteSize"], output.stat().st_size)
            self.assertEqual(asset["variants"][0]["sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            for card_path in (content / "cards").glob("*.json"):
                self.assertEqual(json.loads(card_path.read_text(encoding="utf-8"))["visual"]["cardBackAssetId"], asset["id"])
