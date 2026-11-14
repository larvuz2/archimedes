// Render stills of the current cut at chosen frames (one bundle, many frames) for a quick look without a full render.
//   node scripts/contact_sheet.mjs OUT_DIR 12,100,350 [scale=0.5] [composition=Marlin]
// Frames can also be beats of the v4 score: "k24,k36.5" (frame = round((0.345 + k*60/104) * 24) + 2).
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';

const [outDir, list, scale = '0.5', id = 'Marlin'] = process.argv.slice(2);
const frames = list.split(',').map((s) => (s.startsWith('k') ? Math.round((0.345 + (Number(s.slice(1)) * 60) / 104) * 24) + 2 : Number(s)));
fs.mkdirSync(outDir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const chromiumOptions = {gl: 'swangle'};
const composition = await selectComposition({serveUrl, id, chromiumOptions});
for (const frame of frames) {
  const output = path.join(outDir, `f${String(frame).padStart(4, '0')}.jpg`);
  await renderStill({composition, serveUrl, frame, output, imageFormat: 'jpeg', jpegQuality: 85, scale: Number(scale), chromiumOptions});
  console.log(output);
}
