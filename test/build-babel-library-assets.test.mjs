import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import test from "node:test";

import { buildBabelLibraryAssets } from "../tools/build-babel-library-assets.mjs";

const execFile = promisify(execFileCallback);

test("converts a Babel source PNG to the asset-catalog WebP path and records its metadata", async (t) => {
  const repositoryRoot = await mkdtemp(path.join(os.tmpdir(), "infinity-arcana-assets-"));
  t.after(() => rm(repositoryRoot, { recursive: true, force: true }));

  const sourceDirectory = path.join(repositoryRoot, "cards", "babel-library");
  const contentDirectory = path.join(repositoryRoot, "packages", "content");
  const catalogPath = path.join(contentDirectory, "assets", "assets.json");
  await mkdir(sourceDirectory, { recursive: true });
  await mkdir(path.dirname(catalogPath), { recursive: true });
  await mkdir(path.join(contentDirectory, "packs"), { recursive: true });
  await writeFile(path.join(contentDirectory, "packs", "knowledge-arcana-vol-1.json"), JSON.stringify({ cardIds: ["babel-library"] }));

  const inputPath = path.join(sourceDirectory, "card-babel-library-front-v1.png");
  await execFile("ffmpeg", [
    "-y",
    "-f",
    "lavfi",
    "-i",
    "color=c=navy:s=4x6",
    "-frames:v",
    "1",
    inputPath
  ]);

  await writeFile(
    catalogPath,
    JSON.stringify(
      {
        schemaVersion: "1.0.0",
        catalogVersion: 2,
        assetRoots: [{ id: "sites-public", basePath: "apps/sites-lite/public/assets" }],
        assets: [
          {
            id: "card-babel-library-front",
            contentVersion: 1,
            status: "planned",
            kind: "card-front",
            defaultVariantId: "display-local",
            variants: [
              {
                id: "display-local",
                usage: "display",
                mimeType: "image/webp",
                width: 4,
                height: 6,
                source: {
                  type: "local",
                  rootId: "sites-public",
                  path: "cards/babel-library/front.webp"
                }
              }
            ]
          }
        ]
      },
      null,
      2
    ) + "\n"
  );

  const before = JSON.parse(await readFile(catalogPath, "utf8"));
  const otherAsset = structuredClone(before.assets[0]);
  otherAsset.id = "card-other-pack-front";
  otherAsset.variants[0].source.path = "cards/other-pack/front.webp";
  before.assets.push(otherAsset);
  await writeFile(catalogPath, JSON.stringify(before));

  const result = await buildBabelLibraryAssets({ repositoryRoot, sourceDirectory, contentDirectory });

  assert.equal(result.convertedAssetIds.length, 1);
  assert.deepEqual(result.convertedAssetIds, ["card-babel-library-front"]);

  const outputPath = path.join(
    repositoryRoot,
    "apps",
    "sites-lite",
    "public",
    "assets",
    "cards",
    "babel-library",
    "front.webp"
  );
  const output = await readFile(outputPath);
  const updatedCatalog = JSON.parse(await readFile(catalogPath, "utf8"));
  const asset = updatedCatalog.assets[0];
  const variant = asset.variants[0];

  assert.equal(asset.status, "available");
  assert.equal(asset.contentVersion, 2);
  assert.equal(updatedCatalog.catalogVersion, 3);
  assert.equal(variant.byteSize, output.length);
  assert.equal(variant.sha256, createHash("sha256").update(output).digest("hex"));
  assert.deepEqual(updatedCatalog.assets[1], otherAsset);
});
