import unittest
from pathlib import Path

from packages.core.infinite_arcana_core.content import filter_cards, load_content
from packages.core.infinite_arcana_core.draw import draw_spread


class CelestialPackTests(unittest.TestCase):
    def test_complete_available_set_can_be_drawn_without_knowledge_cards(self):
        content = load_content(Path("packages/content"))
        cards = filter_cards(content.cards, pack_ids={"celestial-arcana-vol-1"}, statuses={"available"})
        self.assertEqual(len(cards), 22)
        self.assertEqual({card["archetypeId"] for card in cards}, {archetype["id"] for archetype in content.archetypes})
        draws = draw_spread(cards, [str(index) for index in range(22)], seed="celestial-complete-set", unique_cards=True, unique_archetypes=True)
        self.assertEqual({draw["cardId"] for draw in draws}, {card["id"] for card in cards})
        for card in cards:
            with self.subTest(card=card["id"]):
                self.assertEqual(card["domainIds"], ["celestial"])
                self.assertEqual(card["visual"]["cardBackAssetId"], "card-celestial-arcana-vol-1-back")
                self.assertTrue(Path(f"cards/celestial-arcana/card-{card['id']}-front-v1.png").is_file())
                meanings = card["localizedContent"]["ja-JP"]["meanings"]
                self.assertNotEqual(meanings["upright"]["core"], meanings["reversed"]["core"])
                self.assertEqual(set(card["localizedContent"]["ja-JP"]["contexts"]), {"work", "relationships", "creativity", "self"})
