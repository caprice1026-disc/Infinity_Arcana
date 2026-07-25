import assert from "node:assert/strict";
import test from "node:test";

import { drawSpread } from "../src/engine.mjs";

test("browser draw engine matches the two-stage constraints", async () => {
  const cards = [
    { id: "a-one", archetypeId: "a" },
    { id: "a-two", archetypeId: "a" },
    { id: "b-one", archetypeId: "b" },
    { id: "c-one", archetypeId: "c" }
  ];
  const first = await drawSpread(cards, ["situation", "obstacle", "advice"], {
    seed: "known-seed",
    uniqueCards: true,
    uniqueArchetypes: true,
    allowReversed: true
  });
  const second = await drawSpread(cards, ["situation", "obstacle", "advice"], {
    seed: "known-seed",
    uniqueCards: true,
    uniqueArchetypes: true,
    allowReversed: true
  });
  assert.deepEqual(first, second);
  assert.equal(new Set(first.map((draw) => draw.cardId)).size, 3);
  assert.equal(new Set(first.map((draw) => draw.archetypeId)).size, 3);
});
