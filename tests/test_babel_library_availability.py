import json
import unittest
from pathlib import Path


class BabelLibraryAvailabilityTests(unittest.TestCase):
    def test_all_knowledge_arcana_cards_are_available_and_share_babel_back(self):
        root = Path("packages/content")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        cards = [json.loads((root / relative).read_text(encoding="utf-8")) for relative in manifest["files"]["cards"]]

        self.assertEqual(len(cards), 22)
        self.assertTrue(all(card["status"] == "available" for card in cards))
        self.assertTrue(all(card["visual"]["cardBackAssetId"] == "card-knowledge-arcana-vol-1-back" for card in cards))

        catalog = json.loads((root / manifest["files"]["assetCatalog"]).read_text(encoding="utf-8"))
        back = next(asset for asset in catalog["assets"] if asset["id"] == "card-knowledge-arcana-vol-1-back")
        self.assertEqual(back["status"], "available")
        self.assertEqual(back["kind"], "card-back")


if __name__ == "__main__":
    unittest.main()
