import { readFile, readdir, access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const schemaDirectory = path.join(repositoryRoot, "packages", "schemas");
const contentDirectory = path.join(repositoryRoot, "packages", "content");

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function formatAjvErrors(errors = []) {
  return errors
    .map((error) => (error.instancePath || "/") + " " + error.message)
    .join("; ");
}

async function validateFile(validator, filePath) {
  const value = await readJson(filePath);
  if (!validator(value)) {
    throw new Error(path.relative(repositoryRoot, filePath) + ": " + formatAjvErrors(validator.errors));
  }
  return value;
}

async function listJsonFiles(directory) {
  return (await readdir(directory, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map((entry) => entry.name)
    .sort();
}

function buildUniqueMap(items, label) {
  const byId = new Map();
  for (const item of items) {
    assert(!byId.has(item.id), "Duplicate " + label + " ID: " + item.id + ".");
    byId.set(item.id, item);
  }
  return byId;
}

async function assertManifestDirectoryMatches(relativePaths, directoryName, label) {
  const listedFiles = relativePaths.map((filePath) => path.basename(filePath)).sort();
  const actualFiles = await listJsonFiles(path.join(contentDirectory, directoryName));
  assert(
    JSON.stringify(listedFiles) === JSON.stringify(actualFiles),
    "Manifest " + label + " file list is incomplete or stale."
  );
}

function assertDefaultLocaleContent(item, label) {
  assert(item.name[item.defaultLocale], item.id + ": default locale is missing from " + label + " name.");
  assert(
    item.localizedContent[item.defaultLocale],
    item.id + ": default locale content is missing from " + label + "."
  );
}

function assertPublication(item, label) {
  if (item.status === "published") {
    assert(item.publication.publishedAt, item.id + ": published " + label + " needs publishedAt.");
  }
}

const schemaFiles = [
  "shared.schema.json",
  "archetype.schema.json",
  "card.schema.json",
  "domain.schema.json",
  "pack.schema.json",
  "spread.schema.json",
  "asset-catalog.schema.json",
  "manifest.schema.json"
];

const schemas = await Promise.all(
  schemaFiles.map((fileName) => readJson(path.join(schemaDirectory, fileName)))
);

const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
for (const schema of schemas) {
  ajv.addSchema(schema);
}

const validateArchetype = ajv.getSchema("urn:infinity-arcana:schema:archetype:1.0.0");
const validateCard = ajv.getSchema("urn:infinity-arcana:schema:card:1.0.0");
const validateDomain = ajv.getSchema("urn:infinity-arcana:schema:domain:1.0.0");
const validatePack = ajv.getSchema("urn:infinity-arcana:schema:pack:1.0.0");
const validateAssetCatalog = ajv.getSchema("urn:infinity-arcana:schema:asset-catalog:1.0.0");
const validateManifest = ajv.getSchema("urn:infinity-arcana:schema:manifest:1.2.0");
const validateSpread = ajv.getSchema("urn:infinity-arcana:schema:spread:1.0.0");

assert(
  validateArchetype &&
    validateCard &&
    validateDomain &&
    validatePack &&
    validateSpread &&
    validateAssetCatalog &&
    validateManifest,
  "Schema compilation failed."
);

const manifest = await validateFile(validateManifest, path.join(contentDirectory, "manifest.json"));

const archetypePaths = manifest.files.archetypes.map((relativePath) =>
  path.join(contentDirectory, relativePath)
);
const cardPaths = manifest.files.cards.map((relativePath) =>
  path.join(contentDirectory, relativePath)
);
const domainPaths = manifest.files.domains.map((relativePath) =>
  path.join(contentDirectory, relativePath)
);
const packPaths = manifest.files.packs.map((relativePath) =>
  path.join(contentDirectory, relativePath)
);
const spreadPaths = manifest.files.spreads.map((relativePath) =>
  path.join(contentDirectory, relativePath)
);
const assetCatalogPath = path.join(contentDirectory, manifest.files.assetCatalog);

const archetypes = await Promise.all(
  archetypePaths.map((filePath) => validateFile(validateArchetype, filePath))
);
const cards = await Promise.all(
  cardPaths.map((filePath) => validateFile(validateCard, filePath))
);
const domains = await Promise.all(
  domainPaths.map((filePath) => validateFile(validateDomain, filePath))
);
const packs = await Promise.all(
  packPaths.map((filePath) => validateFile(validatePack, filePath))
);
const spreads = await Promise.all(
  spreadPaths.map((filePath) => validateFile(validateSpread, filePath))
);
const assetCatalog = await validateFile(validateAssetCatalog, assetCatalogPath);

assert(archetypes.length === 22, "Expected 22 archetypes, found " + archetypes.length + ".");
assert(
  manifest.counts.archetypes === archetypes.length,
  "Manifest archetype count does not match loaded content."
);
assert(manifest.counts.cards === cards.length, "Manifest card count does not match loaded content.");
assert(
  manifest.counts.domains === domains.length,
  "Manifest domain count does not match loaded content."
);
assert(manifest.counts.packs === packs.length, "Manifest pack count does not match loaded content.");
assert(manifest.counts.spreads === spreads.length, "Manifest spread count does not match loaded content.");
assert(
  manifest.counts.assets === assetCatalog.assets.length,
  "Manifest asset count does not match loaded content."
);

const archetypeById = buildUniqueMap(archetypes, "archetype");
const cardById = buildUniqueMap(cards, "card");
const domainById = buildUniqueMap(domains, "domain");
const packById = buildUniqueMap(packs, "pack");

const archetypeNumbers = new Set(archetypes.map((archetype) => archetype.majorArcanaNumber));
assert(archetypeNumbers.size === 22, "Major arcana numbers must be unique.");
for (let number = 0; number <= 21; number += 1) {
  assert(archetypeNumbers.has(number), "Missing major arcana number " + number + ".");
}

for (const archetype of archetypes) {
  assertDefaultLocaleContent(archetype, "archetype");
  assert(
    archetype.inheritancePolicy.minimumRequiredThemeMatches <=
      archetype.semanticAnchors.requiredThemeIds.length,
    archetype.id + ": minimumRequiredThemeMatches exceeds required themes."
  );
  assertPublication(archetype, "archetype");
}

for (const domain of domains) {
  assertDefaultLocaleContent(domain, "domain");
  assert(domain.description[domain.defaultLocale], domain.id + ": default locale is missing from description.");
  assertPublication(domain, "domain");
}

await assertManifestDirectoryMatches(manifest.files.archetypes, "archetypes", "archetype");
await assertManifestDirectoryMatches(manifest.files.cards, "cards", "card");
await assertManifestDirectoryMatches(manifest.files.domains, "domains", "domain");
await assertManifestDirectoryMatches(manifest.files.packs, "packs", "pack");
await assertManifestDirectoryMatches(manifest.files.spreads, "spreads", "spread");

const assetRoots = buildUniqueMap(assetCatalog.assetRoots, "asset root");
const assets = buildUniqueMap(assetCatalog.assets, "asset");

for (const asset of assetCatalog.assets) {
  const variantIds = new Set(asset.variants.map((variant) => variant.id));
  assert(variantIds.size === asset.variants.length, asset.id + ": variant IDs must be unique.");
  assert(variantIds.has(asset.defaultVariantId), asset.id + ": defaultVariantId does not exist.");

  for (const variant of asset.variants) {
    if (variant.source.type === "local") {
      const root = assetRoots.get(variant.source.rootId);
      assert(root, asset.id + "/" + variant.id + ": unknown asset root " + variant.source.rootId + ".");
      if (asset.status === "available") {
        await access(path.join(repositoryRoot, root.basePath, variant.source.path));
      }
    }
  }
}

for (const card of cards) {
  const archetype = archetypeById.get(card.archetypeId);
  assert(archetype, card.id + ": unknown archetype " + card.archetypeId + ".");

  const inheritedMatches = card.inheritedThemeIds.filter((themeId) =>
    archetype.semanticAnchors.requiredThemeIds.includes(themeId)
  );
  assert(
    inheritedMatches.length >= archetype.inheritancePolicy.minimumRequiredThemeMatches,
    card.id + ": does not inherit enough required themes from " + archetype.id + "."
  );
  assert(
    !card.inheritedThemeIds.some((themeId) =>
      archetype.semanticAnchors.prohibitedThemeIds.includes(themeId)
    ),
    card.id + ": inherits a prohibited theme from " + archetype.id + "."
  );

  for (const domainId of card.domainIds) {
    assert(domainById.has(domainId), card.id + ": unknown domain " + domainId + ".");
  }
  for (const packId of card.packIds) {
    const pack = packById.get(packId);
    assert(pack, card.id + ": unknown pack " + packId + ".");
    assert(pack.cardIds.includes(card.id), card.id + ": pack " + packId + " does not list this card.");
  }

  const referencedAssetIds = [
    card.visual.primaryAssetId,
    ...card.visual.alternateAssetIds,
    ...(card.visual.cardBackAssetId ? [card.visual.cardBackAssetId] : [])
  ];
  for (const assetId of referencedAssetIds) {
    assert(assets.has(assetId), card.id + ": unknown visual asset " + assetId + ".");
  }
  assert(
    assets.get(card.visual.primaryAssetId).kind === "card-front",
    card.id + ": primary visual asset must be a card-front."
  );
  if (card.visual.cardBackAssetId) {
    assert(assets.has(card.visual.cardBackAssetId), card.id + ": unknown card-back asset " + card.visual.cardBackAssetId + ".");
    assert(assets.get(card.visual.cardBackAssetId).kind === "card-back", card.id + ": cardBackAssetId must reference a card-back.");
  }

  assertDefaultLocaleContent(card, "card");
  assertPublication(card, "card");
  if (card.status === "published") {
    assert(
      assets.get(card.visual.primaryAssetId).status === "available",
      card.id + ": published card needs an available primary asset."
    );
  }
}

for (const pack of packs) {
  assertDefaultLocaleContent(pack, "pack");
  assert(pack.subtitle[pack.defaultLocale], pack.id + ": default locale is missing from subtitle.");
  assert(pack.description[pack.defaultLocale], pack.id + ": default locale is missing from description.");
  assertPublication(pack, "pack");

  if (pack.accessPolicy.accessLevel === "free") {
    assert(pack.accessPolicy.entitlementId === null, pack.id + ": free pack must not require an entitlement.");
  }
  if (pack.accessPolicy.accessLevel === "premium") {
    assert(pack.accessPolicy.entitlementId, pack.id + ": premium pack needs an entitlementId.");
  }

  for (const domainId of pack.domainIds) {
    assert(domainById.has(domainId), pack.id + ": unknown domain " + domainId + ".");
  }

  const coverAsset = assets.get(pack.coverAssetId);
  assert(coverAsset, pack.id + ": unknown cover asset " + pack.coverAssetId + ".");
  assert(coverAsset.kind === "pack-cover", pack.id + ": cover asset must be a pack-cover.");

  assert(
    pack.cardIds.length === pack.compositionPolicy.expectedCardCount,
    pack.id + ": card count does not match compositionPolicy.expectedCardCount."
  );

  const packCards = pack.cardIds.map((cardId) => {
    const card = cardById.get(cardId);
    assert(card, pack.id + ": unknown card " + cardId + ".");
    assert(card.packIds.includes(pack.id), pack.id + ": card " + cardId + " does not reference this pack.");
    for (const domainId of pack.domainIds) {
      assert(
        card.domainIds.includes(domainId),
        pack.id + ": card " + cardId + " does not inherit pack domain " + domainId + "."
      );
    }
    return card;
  });

  const packArchetypeIds = packCards.map((card) => card.archetypeId);
  const uniquePackArchetypeIds = new Set(packArchetypeIds);
  if (!pack.compositionPolicy.allowDuplicateArchetypes) {
    assert(
      uniquePackArchetypeIds.size === packArchetypeIds.length,
      pack.id + ": duplicate archetypes are not allowed."
    );
  }

  if (pack.compositionPolicy.type === "one-per-major-archetype") {
    assert(pack.cardIds.length === 22, pack.id + ": complete major set must contain 22 cards.");
    assert(
      uniquePackArchetypeIds.size === 22,
      pack.id + ": complete major set must contain each archetype exactly once."
    );
    for (const archetypeId of archetypeById.keys()) {
      assert(
        uniquePackArchetypeIds.has(archetypeId),
        pack.id + ": complete major set is missing archetype " + archetypeId + "."
      );
    }
  }

  if (pack.status === "published") {
    assert(coverAsset.status === "available", pack.id + ": published pack needs an available cover.");
    for (const card of packCards) {
      assert(card.status === "published", pack.id + ": published pack contains unpublished card " + card.id + ".");
    }
  }
}

console.log(
  "Validated " +
    archetypes.length +
    " archetypes, " +
    cards.length +
    " cards, " +
    domains.length +
    " domain, " +
    packs.length +
    " pack, " +
    spreads.length +
    " spreads, and " +
    assetCatalog.assets.length +
    " assets."
);
console.log("Content validation passed.");
