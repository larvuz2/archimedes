// Animatic v4.0 — the client-approved "new structure" (docs/proposals/v4-structure), cut to the score.
// Everything lands on beats of the music: t(k) = T0 + k * 60/BPM. scripts/build_audio_v4.py uses the same numbers.
export const VERSION = 'ANIMATIC v4.0';
export const V4 = {width: 1920, height: 1080, fps: 24};
export const BPM = 104;
export const BEAT = 60 / BPM;
export const T0 = 0.345; // first beat of the score
export const tk = (k: number) => T0 + k * BEAT; // beat -> seconds
export const fk = (k: number) => Math.round(tk(k) * V4.fps); // beat -> frame

// Section anchors (beats)
export const K = {hook: 0, waits: 8, hit2: 12, pre: 20, detect: 24, isolate: 36, breakdown: 56, surveil: 60, finale: 80, w1: 84, w2: 88, w3: 92, end: 96};

export type Section = {n: string; name: string; k0: number; k1: number};
export const SECTIONS: Section[] = [
  {n: '01', name: 'The boat', k0: -1, k1: K.waits},
  {n: '02', name: 'Marlin waits', k0: K.waits, k1: K.detect},
  {n: '03', name: 'Detect', k0: K.detect, k1: K.isolate},
  {n: '04', name: 'Isolate', k0: K.isolate, k1: K.surveil},
  {n: '05', name: 'Surveil', k0: K.surveil, k1: K.finale},
  {n: '06', name: 'Coverage · three words', k0: K.finale, k1: K.end},
  {n: '07', name: 'End card', k0: K.end, k1: 200},
];

// Hits in the sound design that the picture answers with a flash and a shake: [beat, strength 0..1]
export const HITS: [number, number][] = [
  [K.hook, 0.5], [K.hit2, 0.35], [K.detect, 1], [K.isolate, 1], [54, 0.6], [K.surveil, 1], [76, 0.5], [K.finale, 0.8], [K.w1, 1], [K.w2, 1], [K.w3, 1], [K.end, 1],
];

// Narration (seconds), mirrors scripts/build_audio_v4.py
export const VO = {
  v01: 1.0, // A boat is running dark for the coast.
  v02: 5.25, // Marlin is already out there.
  v03: 8.1, // Waiting.
  v04: 9.9, // Always ready.
  v05: 14.75, // It detects the contact.
  v06: 21.75, // The nearest Marlins vector in.
  v07: 24.45, // Fifty miles in thirty minutes.
  v08: 30.55, // They isolate the contact.
  v09: 35.7, // And they stay on it.
  v10: 38.5, // Until partners arrive.
  v14: tk(K.end) + 0.62, // Marlin.
};

export const DISCLAIMER_V4 =
  '[PERFORMANCE DISCLAIMER: Archimedes to supply] Concept visualization. 50 nm in 30 min is a design target, not demonstrated performance.';
export const CONTACT_V4 = '[DEMO REQUEST · CONTACT]';
