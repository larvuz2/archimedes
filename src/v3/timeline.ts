// Animatic v3.0 — Storyboard V5 (client "Storyboard 2.0"), 12 shots, 24 fps.
// Shot numbers, timings, VO and supers follow the storyboard exactly. Audio timings mirror scripts/build_audio_v3.py.
export const VERSION = 'ANIMATIC v3.0';
export const V3 = {width: 1920, height: 1080, fps: 24};

export type ShotV3 = {n: string; name: string; start: number; end: number; kind: '3D' | '2D'};
export const SHOTS_V3: ShotV3[] = [
  {n: '01', name: 'The boat', start: 0, end: 4, kind: '3D'},
  {n: '02', name: 'Aircraft radar', start: 4, end: 7, kind: '2D'},
  {n: '03', name: 'Infrared ID', start: 7, end: 10, kind: '3D'},
  {n: '04', name: 'Out of reach', start: 10, end: 16, kind: '2D'},
  {n: '05', name: 'On station', start: 16, end: 20, kind: '2D'},
  {n: '06', name: 'Loiter', start: 20, end: 23, kind: '3D'},
  {n: '07', name: 'Lift', start: 23, end: 28, kind: '3D'},
  {n: '08', name: 'Converge', start: 28, end: 34, kind: '2D'},
  {n: '09', name: 'The run', start: 34, end: 40, kind: '3D'},
  {n: '10', name: 'Eyes on', start: 40, end: 46, kind: '3D'},
  {n: '11', name: 'The fleet', start: 46, end: 56, kind: '2D'},
  {n: '12', name: 'End card', start: 56, end: 60, kind: '2D'},
];

export const T = {
  radarPasses: [4.35, 5.1, 5.85, 6.6], // the return is painted on every sweep
  radarHook: 6.05, // operator hooks it
  irSettle: 7.9, // slew has settled on the contact
  mpaBreaks: 12.8, // aircraft breaks off for home
  trackDashed: 13.4, // track goes dashed (score drops to silence)
  fleetOn: 16.0, // twenty markers blink on
  trackUpdates: [28.6, 30.1, 31.6, 33.1],
  irFull: [40.0, 41.5] as const, // Marlin's own infrared view, then pull out
  surveil: 42.0,
  respace: 47.4,
  vo: {vo1: 23.3, vo2: 42.0, vo3: 52.0, vo4: 57.1},
  vo3Words: [0, 0.75, 1.72], // "Cover." "Sprint." "Persist."
  logoLands: 56.75, // after a beat of silence
};

export const DISCLAIMER_V3 =
  '[PERFORMANCE DISCLAIMER: Archimedes to supply] Concept visualization. 50 nm in 30 min and hull-borne shadowing are design targets, not demonstrated performance.';
export const CONTACT_V3 = '[DEMO REQUEST · CONTACT]';
