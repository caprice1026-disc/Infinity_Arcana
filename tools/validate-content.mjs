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
    .map((error) => `${error.instancePath || "/"} ${error.message}`)
    .join("; ");
}

async function validateFile(validator, filePath) {
  const value = await readJson(filePath);
  if (!validator(value)) {
    throw new Error(`${path.relative(repositoryRoot, filePath)}: ${formatAjvErrors(validator.errors)}`);
  }
  return value;
}

async function listJsonFiles(directory) {
  return (await readdir(directory, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map((entry) => entry.name)
    .sort();
}

const schemaFiles = [
  "shared.schema.json",
  "archetype.schema.json",
  "card.schema.json",
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
const validateAssetCatalog = ajv.getSchema("urn:infinity-arcana:schema:asset-catalog:1.0.0");
const validateManifest = ajv.getSchema("urn:infinity-arcana:schema:manifest:1.0.0");

assert(validateArchetype && validateCard && validateAssetCatalog && validateManifest, "Schema compilation failed.");

const manifest = await validateFile(validateManifest, path.join(contentDirectory, "manifest.json"));

const archetypePaths = manifest.files.archetypes.map((relativePath) => path.join(contentDirectory, relativePath));
const cardPaths = manifest.files.cards.map((relativePath) => path.join(contentDirectory, relativePath));
const assetCatalogPath = path.join(contentDirectory, manifest.files.assetCatalog);

const archetypes = await Promise.all(archetypePaths.map((filePath) => validateFile(validateArchetype, filePath)));
const cards = await Promise.all(cardPaths.map((filePath) => validateFile(validateCard, filePath)));
const assetCatalog = await validateFile(validateAssetCatalog, assetCatalogPath);

assert(archetypes.length === 22, `Expected 22 archetypes, found ${archetypes.length}.`);
assert(manifest.counts.archetypes === archetypes.length, "Manifest archetype count does not match loaded content.");
assert(manifest.counts.cards === cards.length, "Manifest card count does not match loaded content.");
assert(manifest.counts.assets === assetCatalog.assets.length, "Manifest asset count does not match loaded content.");

const archetypeIds = new Set(archetypes.map((archetype) => archetype.id));
const archetypeNumbers = new Set(archetypes.map((archetype) => archetype.majorArcanaNumber));
assert(archetypeIds.size === 22, "Archetype IDs must be unique.");
assert(archetypeNumbers.size === 22, "Major arcana numbers must be unique.");
for (let number = 0; number <= 21; number += 1) {
  assert(archetypeNumbers.has(number), `Missing major arcana number ${number}.`);
}

for (const archetype of archetypes) {
  assert(archetype.name[archetype.defaultLocale], `${archetype.id}: default locale is missing from name.`);
  assert(archetype.localizedContent[archetype.defaultLocale], `${archetype.id}: default locale content is missing.`);
  assert(
    archetype.inheritancePolicy.minimumRequiredThemeMatches <= archetype.semanticAnchors.requiredThemeIds.length,
    `${archetype.id}: minimumRequiredThemeMatches exceeds required themes.`
  );
  if (archetype.status === "published") {
    assert(archetype.publication.publishedAt, `${archetype.id}: published archetype needs publishedAt.`);
  }
}

const listedArchetypeFiles = manifest.files.archetypes.map((filePath) => path.basename(filePath)).sort();
const actualArchetypeFiles = await listJsonFiles(path.join(contentDirectory, "archetypes"));
assert(JSON.stringify(listedArchetypeFiles) === JSON.stringify(actualArchetypeFiles), "Manifest archetype file list is incomplete or stale.");

const listedCardFiles = manifest.files.cards.map((filePath) => path.basename(filePath)).sort();
const actualCardFiles = await listJsonFiles(path.join(contentDirectory, "cards"));
assert(JSON.stringify(listedCardFiles) === JSON.stringify(actualCardFiles), "Manifest card file list is incomplete or stale.");

const assetRoots = new Map(assetCatalog.assetRoots.map((root) => [root.id, root]));
assert(assetRoots.size === assetCatalog.assetRoots.length, "Asset root IDs must be unique.");

const assets = new Map();
for (const asset of assetCatalog.assets) {
  assert(!assets.has(asset.id), `Duplicate asset ID: ${asset.id}.`);
  assets.set(asset.id, asset);

  const variantIds = new Set(asset.variants.map((variant) => variant.id));
  assert(variantIds.size === asset.variants.length, `${asset.id}: variant IDs must be unique.`);
  assert(variantIds.has(asset.defaultVariantId), `${asset.id}: defaultVariantId does not exist.`);

  for (const variant of asset.variants) {
    if (variant.source.type === "local") {
      const root = assetRoots.get(variant.source.rootId);
      assert(root, `${asset.id}/${variant.id}: unknown asset root ${variant.source.rootId}.`);
      if (asset.status === "available") {
        await access(path.join(repositoryRoot, root.basePath, variant.source.path));
      }
    }
  }
}

const archetypeById = new Map(archetypes.map((archetype) => [archetype.id, archetype]));
for (const card of cards) {
  const archetype = archetypeById.get(card.archetypeId);
  assert(archetype, `${card.id}: unknown archetype ${card.archetypeId}.`);

  const inheritedMatches = card.inheritedThemeIds.filter((themeId) =>
    archetype.semanticAnchors.requiredThemeIds.includes(themeId)
  );
  assert(
    inheritedMatches.length >= archetype.inheritancePolicy.minimumRequiredThemeMatches,
    `${card.id}: does not inherit enough required themes from ${archetype.id}.`
  );
  assert(
    !card.inheritedThemeIds.some((themeId) => archetype.semanticAnchors.prohibitedThemeIds.includes(themeId)),
    `${card.id}: inherits a prohibited theme from ${archetype.id}.`
  );

  const referencedAssetIds = [
    card.visual.primaryAssetId,
    ...card.visual.alternateAssetIds,
    ...(card.visual.cardBackAssetId ? [card.visual.cardBackAssetId] : [])
  ];
  for (const assetId of referencedAssetIds) {
    assert(assets.has(assetId), `${card.id}: unknown visual asset ${assetId}.`);
  }

  assert(card.name[card.defaultLocale], `${card.id}: default locale is missing from name.`);
  assert(card.localizedContent[card.defaultLocale], `${card.id}: default locale content is missing.`);
  if (card.status === "published") {
    assert(card.publication.publishedAt, `${card.id}: published card needs publishedAt.`);
    assert(assets.get(card.visual.primaryAssetId).status === "available", `${card.id}: published card needs an available primary asset.`);
  }
}

console.log(`Validated ${archetypes.length} archetypes, ${cards.length} card, and ${assetCatalog.assets.length} asset.`);
console.log("Content validation passed.");
