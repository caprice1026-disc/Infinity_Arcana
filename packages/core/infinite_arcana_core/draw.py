"""Balanced two-stage card drawing with a portable seeded random source."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable


class CandidateExhaustedError(ValueError):
    """Raised when the remaining candidates cannot satisfy a spread constraint."""


class Sha256CounterRandom:
    """`sha256-counter-v1`: deterministic values in [0, 1) from a string seed."""

    algorithm_id = "sha256-counter-v1"

    def __init__(self, seed: str):
        self.seed = seed
        self.counter = 0

    def next(self) -> float:
        payload = f"{self.seed}:{self.counter}".encode("utf-8")
        self.counter += 1
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / 2**64


def draw_spread(
    cards: Iterable[dict[str, Any]],
    positions: Iterable[str],
    *,
    seed: str,
    unique_cards: bool,
    unique_archetypes: bool,
    allow_reversed: bool = True,
    reversed_probability: float = 0.5,
) -> list[dict[str, str]]:
    """Draw positions by choosing an archetype uniformly, then a card uniformly."""

    if not 0 <= reversed_probability <= 1:
        raise ValueError("reversed_probability must be between 0 and 1")
    random_source = Sha256CounterRandom(seed)
    remaining = sorted((dict(card) for card in cards), key=lambda card: card["id"])
    draws: list[dict[str, str]] = []
    for position_id in positions:
        by_archetype: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for card in remaining:
            by_archetype[card["archetypeId"]].append(card)
        archetype_ids = sorted(by_archetype)
        if not archetype_ids:
            raise CandidateExhaustedError(f"Not enough candidate cards for position '{position_id}'.")
        archetype_id = archetype_ids[int(random_source.next() * len(archetype_ids))]
        candidates = sorted(by_archetype[archetype_id], key=lambda card: card["id"])
        card = candidates[int(random_source.next() * len(candidates))]
        orientation = "reversed" if allow_reversed and random_source.next() < reversed_probability else "upright"
        draws.append(
            {"positionId": position_id, "cardId": card["id"], "archetypeId": archetype_id, "orientation": orientation}
        )
        if unique_cards or unique_archetypes:
            remaining = [
                candidate
                for candidate in remaining
                if candidate["id"] != card["id"] and (not unique_archetypes or candidate["archetypeId"] != archetype_id)
            ]
    return draws
