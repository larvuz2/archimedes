import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

// Fonts are bundled in public/fonts so renders never depend on the network.
// Swap for Archimedes brand fonts when supplied.
const faces: [string, string, string, string][] = [
  ['IBM Plex Sans', 'ibm-plex-sans-latin-400-normal.woff2', '400', 'normal'],
  ['IBM Plex Sans', 'ibm-plex-sans-latin-400-italic.woff2', '400', 'italic'],
  ['IBM Plex Sans', 'ibm-plex-sans-latin-600-normal.woff2', '600', 'normal'],
  ['IBM Plex Sans', 'ibm-plex-sans-latin-700-normal.woff2', '700', 'normal'],
  ['IBM Plex Mono', 'ibm-plex-mono-latin-400-normal.woff2', '400', 'normal'],
  ['IBM Plex Mono', 'ibm-plex-mono-latin-500-normal.woff2', '500', 'normal'],
];

for (const [family, file, weight, style] of faces) {
  loadFont({family, url: staticFile(`fonts/${file}`), weight, style});
}
