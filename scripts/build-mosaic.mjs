// scripts/build-mosaic.mjs
//
// One-off generator for the repeating role-portrait mosaic background used
// on the index page's role preview section (matching the technique used on
// dota2.com/home: a single small tile image with `background-repeat:
// repeat`, where the second row is pre-offset by half a tile-width so the
// repeating tile reads as a continuous brick/masonry pattern instead of an
// aligned grid).
//
// Usage: node scripts/build-mosaic.mjs

import sharp from 'sharp';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const CELL = 160; // px, each square portrait crop
const COLS = 8; // portraits per row, full width
const rolesData = JSON.parse(await readFile('src/data/roles.json', 'utf-8'));

const portraits = rolesData
  .filter((r) => r.set === 'Standard' && r.portraitUrl)
  .map((r) => path.join('public', r.portraitUrl));

// Row 1: COLS portraits, aligned to the grid.
// Row 2: COLS + 1 portraits, shifted left by half a cell so it starts/ends
// half-cut -- this half-cell offset is what creates the brick pattern when
// the whole tile repeats.
const row1Count = COLS;
const row2Count = COLS + 1;
const needed = row1Count + row2Count;

if (portraits.length < needed) {
  throw new Error(`Need at least ${needed} Standard portraits, found ${portraits.length}`);
}

// Pick a spread of portraits across the list rather than the first N, so the
// tile doesn't look like an alphabetical run.
function pickSpread(arr, count) {
  const step = arr.length / count;
  return Array.from({ length: count }, (_, i) => arr[Math.floor(i * step)]);
}

const chosen = pickSpread(portraits, needed);
const row1 = chosen.slice(0, row1Count);
const row2 = chosen.slice(row1Count);

const tileWidth = COLS * CELL;
const tileHeight = 2 * CELL;

async function squareCrop(filePath) {
  return sharp(filePath).resize(CELL, CELL, { fit: 'cover' }).toBuffer();
}

const row1Buffers = await Promise.all(row1.map(squareCrop));
const row2Buffers = await Promise.all(row2.map(squareCrop));

const composites = [
  ...row1Buffers.map((buf, i) => ({ input: buf, left: i * CELL, top: 0 })),
  ...row2Buffers.map((buf, i) => ({ input: buf, left: i * CELL - CELL / 2, top: CELL })),
];

const tile = sharp({
  create: {
    width: tileWidth,
    height: tileHeight,
    channels: 3,
    background: '#18120a',
  },
})
  .composite(composites)
  .extract({ left: 0, top: 0, width: tileWidth, height: tileHeight });

const outPath = 'public/images/roles-mosaic.webp';
await tile.webp({ quality: 80 }).toFile(outPath);

console.log(`Wrote ${outPath} (${tileWidth}x${tileHeight} tile, repeats seamlessly)`);
