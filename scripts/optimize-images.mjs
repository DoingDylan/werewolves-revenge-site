// scripts/optimize-images.mjs
//
// Repeatable batch optimizer for game artwork exported by export_roles.py
// (role portraits/images in public/images/roles, ability icons in
// public/images/abilities). Converts every PNG to WebP, downscaling
// anything larger than MAX_DIMENSION (these only ever render as small grid
// thumbnails or a single detail-page portrait/icon, so the original
// full-resolution exports are massive overkill), then deletes the source
// PNG once its .webp replacement is written.
//
// Usage: npm run optimize-images

import { readdir, stat, mkdir, unlink } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const DIRS = [path.resolve('public/images/roles'), path.resolve('public/images/abilities')];
const MAX_DIMENSION = 1000; // px, longest edge
const WEBP_QUALITY = 82;

async function optimizeDir(dir) {
  await mkdir(dir, { recursive: true });

  const entries = await readdir(dir);
  const pngFiles = entries.filter((f) => f.toLowerCase().endsWith('.png'));

  console.log(`Found ${pngFiles.length} PNGs in ${dir}`);

  let totalBefore = 0;
  let totalAfter = 0;
  let converted = 0;

  for (const file of pngFiles) {
    const inputPath = path.join(dir, file);
    const outputPath = path.join(dir, file.replace(/\.png$/i, '.webp'));

    const { size: beforeSize } = await stat(inputPath);

    await sharp(inputPath)
      .resize({
        width: MAX_DIMENSION,
        height: MAX_DIMENSION,
        fit: 'inside',
        withoutEnlargement: true,
      })
      .webp({ quality: WEBP_QUALITY })
      .toFile(outputPath);

    const { size: afterSize } = await stat(outputPath);
    await unlink(inputPath);

    totalBefore += beforeSize;
    totalAfter += afterSize;
    converted++;

    if (converted % 100 === 0) {
      console.log(`...${converted}/${pngFiles.length}`);
    }
  }

  const mb = (bytes) => (bytes / 1024 / 1024).toFixed(1);
  console.log(`Converted ${converted} images. Before: ${mb(totalBefore)} MB, After: ${mb(totalAfter)} MB\n`);
}

for (const dir of DIRS) {
  await optimizeDir(dir);
}

console.log(`Original PNGs have been deleted now that their .webp replacements exist.`);
