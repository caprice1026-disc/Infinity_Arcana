import assert from "node:assert/strict";
import test from "node:test";

import { drawSpread } from "../src/engine.mjs";
import { exportStore, openStore } from "../src/storage.mjs";

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
  assert.deepEqual(first, [
    { positionId: "situation", cardId: "a-one", archetypeId: "a", orientation: "reversed" },
    { positionId: "obstacle", cardId: "c-one", archetypeId: "c", orientation: "upright" },
    { positionId: "advice", cardId: "b-one", archetypeId: "b", orientation: "reversed" }
  ]);
});

test("storage survives export and import when IndexedDB is unavailable", async () => {
  const values = new Map();
  globalThis.localStorage = {
    getItem(key) { return values.get(key) ?? null; },
    setItem(key, value) { values.set(key, String(value)); }
  };
  const store = await openStore();
  await store.put("readings", { id: "reading-1", question: "問い", draws: [] });
  await store.put("collection", { id: "card-1", cardId: "card-1" });
  const exported = await exportStore(store);
  assert.equal(exported.readings[0].question, "問い");
  const imported = await openStore();
  await imported.replaceAll(exported);
  assert.equal((await imported.all("collection"))[0].cardId, "card-1");
});
