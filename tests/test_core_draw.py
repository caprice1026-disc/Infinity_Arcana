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
        self.assertEqual(first, [
            {"positionId": "situation", "cardId": "a-one", "archetypeId": "a", "orientation": "reversed"},
            {"positionId": "obstacle", "cardId": "c-one", "archetypeId": "c", "orientation": "upright"},
            {"positionId": "advice", "cardId": "b-one", "archetypeId": "b", "orientation": "reversed"},
        ])

    def test_reversed_probability_and_candidate_exhaustion_are_explicit(self):
        cards = [{"id": "a-one", "archetypeId": "a"}]
        upright = draw_spread(cards, ["guidance"], seed="seed", unique_cards=True, unique_archetypes=True, reversed_probability=0)
        self.assertEqual(upright[0]["orientation"], "upright")
        with self.assertRaisesRegex(ValueError, "position 'second'"):
            draw_spread(cards, ["guidance", "second"], seed="seed", unique_cards=True, unique_archetypes=True)

    def test_uniform_archetype_sampling_has_no_large_small_sample_skew(self):
        cards = [{"id": f"{name}-one", "archetypeId": name} for name in ("a", "b", "c")]
        counts = {name: 0 for name in ("a", "b", "c")}
        for index in range(900):
            draw = draw_spread(cards, ["guidance"], seed=f"stat-{index}", unique_cards=True, unique_archetypes=True, allow_reversed=False)[0]
            counts[draw["archetypeId"]] += 1
        self.assertTrue(all(240 <= count <= 360 for count in counts.values()), counts)
