import unittest

from packages.core.infinite_arcana_core.draw import draw_spread


class CoreDrawTests(unittest.TestCase):
    def test_seeded_three_card_draw_is_reproducible_and_has_unique_cards_and_archetypes(self):
        cards = [
            {"id": "a-one", "archetypeId": "a"},
            {"id": "a-two", "archetypeId": "a"},
            {"id": "b-one", "archetypeId": "b"},
            {"id": "c-one", "archetypeId": "c"},
        ]
        positions = ["situation", "obstacle", "advice"]

        first = draw_spread(cards, positions, seed="known-seed", unique_cards=True, unique_archetypes=True)
        second = draw_spread(cards, positions, seed="known-seed", unique_cards=True, unique_archetypes=True)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len({draw["cardId"] for draw in first}), 3)
        self.assertEqual(len({draw["archetypeId"] for draw in first}), 3)
        self.assertEqual([draw["positionId"] for draw in first], positions)
