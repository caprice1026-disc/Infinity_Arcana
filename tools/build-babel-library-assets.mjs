import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const modulePath = fileURLToPath(import.meta.url);
const defaultRepositoryRoot = path.resolve(path.dirname(modulePath), "..");

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

function runCommand(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(command + " exited with code " + code + ".\n" + stderr.trim()));
    });
  });
}

async function measureImage(filePath, ffprobePath) {
  const output = [];
  await new Promise((resolve, reject) => {
    const child = spawn(
      ffprobePath,
      [
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        filePath
      ],
      { stdio: ["ignore", "pipe", "pipe"] }
    );
    let stderr = "";
    child.stdout.on("data", (chunk) => output.push(chunk));
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(ffprobePath + " exited with code " + code + ".\n" + stderr.trim()));
    });
  });

  const stream = JSON.parse(Buffer.concat(output).toString("utf8")).streams?.[0];
  if (!stream?.width || !stream?.height) {
    throw new Error("Could not measure generated image: " + filePath);
  }
  return { width: stream.width, height: stream.height };
}

function getSourceFileName(assetId, sourceNames) {
  const match = /^card-(.+)-front$/.exec(assetId);
  if (!match) {
    throw new Error("Card front asset ID must be card-<slug>-front: " + assetId);
  }
  const prefix = "card-" + match[1] + "-front-";
  const matchingNames = sourceNames.filter((name) => name.startsWith(prefix) && name.endsWith(".png"));
  if (matchingNames.length !== 1) {
    throw new Error(
      assetId + ": expected exactly one source PNG matching " + prefix + "*.png, found " + matchingNames.length + "."
    );
  }
  return matchingNames[0];
}

async function getBuildTargets(catalog, sourceDirectory, repositoryRoot) {
  const rootsById = new Map(catalog.assetRoots.map((root) => [root.id, root]));
  const sourceNames = await readdir(sourceDirectory);
  const targets = [];

  for (const asset of catalog.assets) {
    if (asset.kind !== "card-front") {
      continue;
    }
    const variant = asset.variants.find((item) => item.id === asset.defaultVariantId);
    if (!variant || variant.source.type !== "local" || variant.mimeType !== "image/webp") {
      throw new Error(asset.id + ": card-front default variant must be a local WebP.");
    }
    const root = rootsById.get(variant.source.rootId);
    if (!root) {
      throw new Error(asset.id + ": unknown asset root " + variant.source.rootId + ".");
    }
    targets.push({
      asset,
      variant,
      inputPath: path.join(sourceDirectory, getSourceFileName(asset.id, sourceNames)),
      outputPath: path.join(repositoryRoot, root.basePath, variant.source.path)
    });
  }
  return targets;
}

async function getFileMetadata(filePath) {
  const [file, fileStat] = await Promise.all([readFile(filePath), stat(filePath)]);
  return {
    byteSize: fileStat.size,
    sha256: createHash("sha256").update(file).digest("hex")
  };
}

export async function buildBabelLibraryAssets({
  repositoryRoot = defaultRepositoryRoot,
  sourceDirectory = path.join(repositoryRoot, "cards", "babel-library"),
  contentDirectory = path.join(repositoryRoot, "packages", "content"),
  ffmpegPath = "ffmpeg",
  ffprobePath = "ffprobe"
} = {}) {
  const catalogPath = path.join(contentDirectory, "assets", "assets.json");
  const catalog = await readJson(catalogPath);
  const targets = await getBuildTargets(catalog, sourceDirectory, repositoryRoot);
  if (targets.length === 0) {
    throw new Error("No local WebP card-front assets were found in the catalog.");
  }

  const metadataByAssetId = new Map();
  for (const target of targets) {
    await mkdir(path.dirname(target.outputPath), { recursive: true });
    await runCommand(ffmpegPath, [
      "-y",
      "-loglevel",
      "error",
      "-i",
      target.inputPath,
      "-frames:v",
      "1",
      "-vf",
      "scale=" + target.variant.width + ":" + target.variant.height + ":flags=lanczos",
      "-c:v",
      "libwebp",
      "-quality",
      "90",
      target.outputPath
    ]);
    const dimensions = await measureImage(target.outputPath, ffprobePath);
    if (dimensions.width !== target.variant.width || dimensions.height !== target.variant.height) {
      throw new Error(
        target.asset.id +
          ": generated " +
          dimensions.width +
          "x" +
          dimensions.height +
          ", expected " +
          target.variant.width +
          "x" +
          target.variant.height +
          "."
      );
    }
    metadataByAssetId.set(target.asset.id, await getFileMetadata(target.outputPath));
  }

  let catalogChanged = false;
  for (const target of targets) {
    const metadata = metadataByAssetId.get(target.asset.id);
    const metadataChanged =
      target.variant.byteSize !== metadata.byteSize || target.variant.sha256 !== metadata.sha256;
    const statusChanged = target.asset.status !== "available";
    if (!metadataChanged && !statusChanged) {
      continue;
    }
    target.variant.byteSize = metadata.byteSize;
    target.variant.sha256 = metadata.sha256;
    target.asset.status = "available";
    target.asset.contentVersion += 1;
    catalogChanged = true;
  }
  if (catalogChanged) {
    catalog.catalogVersion += 1;
    await writeFile(catalogPath, JSON.stringify(catalog, null, 2) + "\n");
  }

  return {
    convertedAssetIds: targets.map((target) => target.asset.id),
    catalogChanged
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === modulePath) {
  buildBabelLibraryAssets()
    .then((result) => {
      console.log(
        "Converted " +
          result.convertedAssetIds.length +
          " Babel Library card PNGs to catalog WebP paths" +
          (result.catalogChanged ? " and updated the asset catalog." : ".")
      );
    })
    .catch((error) => {
      console.error(error.message);
      process.exitCode = 1;
    });
}
