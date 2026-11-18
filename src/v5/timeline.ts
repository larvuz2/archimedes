// Animatic v5.0: Storyboard V7 ("Intercept. Surveil. Stop."), 14 shots, cut on the beat grid of the score.
// The score runs at exactly 104 BPM with its first beat at 0.055 s: t(k) = T0 + k * BEAT. scripts/build_audio_v5.py uses the same grid.
export const VERSION = 'ANIMATIC v5.1';
export const V5 = {width: 1920, height: 1080, fps: 24};
export const BEAT = 60 / 104;
export const T0 = 0.055;
export const tk = (k: number) => T0 + k * BEAT; // beat -> seconds
export const fk = (k: number) => Math.round(tk(k) * V5.fps); // beat -> frame

// The 14 storyboard shots, snapped to the nearest beat of the storyboard timecode (all within 0.35 s of it).
export type Shot = {n: string; name: string; act: string; k0: number; k1: number};
export const SHOTS: Shot[] = [
  {n: '01', name: 'The boat', act: 'Act 1 · The gap', k0: 0, k1: 7},
  {n: '02', name: 'Detected and designated', act: 'Act 1 · The gap', k0: 7, k1: 16},
  {n: '03', name: 'No end game', act: 'Act 1 · The gap', k0: 16, k1: 24},
  {n: '04', name: 'Tasked', act: 'Act 2 · Intercept', k0: 24, k1: 32},
  {n: '05', name: 'Lift', act: 'Act 2 · Intercept', k0: 32, k1: 38},
  {n: '06', name: 'Converge', act: 'Act 2 · Intercept', k0: 38, k1: 45},
  {n: '07', name: 'Eyes on', act: 'Act 2 · Intercept', k0: 45, k1: 54},
  {n: '08', name: 'Authorized', act: 'Act 3 · The stop', k0: 54, k1: 60},
  {n: '09', name: 'Pass', act: 'Act 3 · The stop', k0: 60, k1: 66},
  {n: '10', name: 'Net away', act: 'Act 3 · The stop', k0: 66, k1: 72},
  {n: '11', name: 'Fouled', act: 'Act 3 · The stop', k0: 72, k1: 80},
  {n: '12', name: 'Hold', act: 'Act 3 · The stop', k0: 80, k1: 88},
  {n: '13', name: 'The fleet', act: 'Act 4 · Coverage', k0: 88, k1: 97},
  {n: '14', name: 'End card', act: 'Act 4 · Coverage', k0: 97, k1: 105},
];
export const shotStart = (n: string) => tk(SHOTS.find((s) => s.n === n)!.k0);

// Story beats inside the shots (seconds)
export const T = {
  radarPasses: [4.6, 5.35, 6.1, 6.85, 7.6, 8.35], // the return is painted on every sweep
  cue: 5.0, // status strip: CUE
  hook: 6.25, // operator hooks the return
  detected: 6.45,
  designated: 7.35,
  mpaBreaks: 11.2, // the aircraft breaks off for home
  trackDashed: 11.9, // the track goes dashed, projected to the coast (score sinks to silence)
  fleetOn: tk(24.5), // twenty markers blink on
  task: tk(28), // C2 tasks the nearest two
  intercept: tk(29), // intercept lines draw
  updates: [tk(39), tk(40.5), tk(42), tk(43.5)], // converge: a track update (and data tone) every 1.5 beats
  irPull: tk(45) + 1.5, // eyes on: the thermal view shrinks into the LIVE inset
  authorized: tk(54) + 0.15, // C2 · STOP AUTHORIZED · PROFILE: V-NET (confirm tone)
  plan: tk(55), // the pass path and the V draw themselves
  netFire: tk(66) + 0.65, // n1 plate fires at 0.9 s; the plate starts 6 frames in
  foul: tk(72) + (1.379 / 0.87), // x1 plate plays at 0.87x; the props foul at 1.379 s plate time
  diw: tk(72) + 3.0, // dead in the water
  respace: tk(89), // the fleet re-spaces
  words: [tk(90), tk(92), tk(94)], // INTERCEPT. SURVEIL. STOP.
  logo: tk(98), // after a beat of silence on navy
};

// Narration (27 words). Start times in seconds; lines follow the storyboard's timecodes.
export const VO = {
  l1ab: tk(32) + 0.12, // "Tasked, the nearest two close" (0:18)
  l1c: tk(38) + 0.1, // "fifty miles in thirty minutes," with the 50 NM · 30 MIN readout (0:22)
  l2: tk(47), // "put eyes on," (0:27)
  l3: tk(60) + 0.3, // "and stop it dead in the water" (0:35)
  l4: tk(80) + 0.45, // "until partners arrive." (0:46)
  l5a: tk(90), // "Intercept." (0:52)
  l5b: tk(92), // "Surveil."
  l5c: tk(94), // "Stop."
  l6: tk(98) + 0.45, // [pause] "Marlin." (0:57)
};

// Hits in the sound design that the picture answers with a flash and a small shake: [beat, strength]
export const HITS: [number, number][] = [[0, 0.4], [32, 1], [45, 0.6], [54, 0.5], [60, 1], [74.75, 0.6], [88, 0.7], [90, 0.9], [92, 0.9], [94, 1], [98, 0.6]];

export const DISCLAIMER_V5 =
  '[PERFORMANCE DISCLAIMER: Archimedes to supply] Concept visualization. 50 nm in 30 min, hull-borne shadowing and the stop shown are design targets, not demonstrated performance. Stop profile is notional and operator-selected.';
export const CONTACT_V5 = '[DEMO REQUEST · CONTACT]';
