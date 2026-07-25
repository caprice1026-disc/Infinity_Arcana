const UINT64_SCALE = 18446744073709551616n;

async function seededValue(seed, counter) {
  const bytes = new TextEncoder().encode(`${seed}:${counter}`);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  const value = new DataView(digest).getBigUint64(0, false);
  return Number(value) / Number(UINT64_SCALE);
}

export async function drawSpread(cards, positions, options) {
  const remaining = [...cards].sort((left, right) => left.id.localeCompare(right.id));
  const draws = [];
  let counter = 0;
  for (const positionId of positions) {
    const groups = new Map();
    for (const card of remaining) {
      if (!groups.has(card.archetypeId)) groups.set(card.archetypeId, []);
      groups.get(card.archetypeId).push(card);
    }
    const archetypeIds = [...groups.keys()].sort();
    if (!archetypeIds.length) throw new Error("Not enough candidate cards for spread constraints.");
    const archetypeId = archetypeIds[Math.floor((await seededValue(options.seed, counter++)) * archetypeIds.length)];
    const candidates = groups.get(archetypeId).sort((left, right) => left.id.localeCompare(right.id));
    const card = candidates[Math.floor((await seededValue(options.seed, counter++)) * candidates.length)];
    const orientation = options.allowReversed && (await seededValue(options.seed, counter++)) < 0.5 ? "reversed" : "upright";
    draws.push({ positionId, cardId: card.id, archetypeId, orientation });
    if (options.uniqueCards || options.uniqueArchetypes) {
      remaining.splice(0, remaining.length, ...remaining.filter((candidate) => candidate.id !== card.id && (!options.uniqueArchetypes || candidate.archetypeId !== archetypeId)));
    }
  }
  return draws;
}
