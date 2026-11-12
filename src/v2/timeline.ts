// Storyboard V5 (client "Storyboard 2.0"): 12 shots, one continuous night, 20-word VO.
// Times in seconds. Shot numbers match the client storyboard.
export const VERSION = 'ANIMATIC v2.0';

export type ShotV2 = {n: string; name: string; start: number; end: number};
export const SHOTS_V2: ShotV2[] = [
  {n: '01', name: 'The boat', start: 0, end: 4},
  {n: '02', name: 'Aircraft radar', start: 4, end: 7},
  {n: '03', name: 'Infrared ID', start: 7, end: 10},
  {n: '04', name: 'Out of reach', start: 10, end: 16},
  {n: '05', name: 'On station', start: 16, end: 20},
  {n: '06', name: 'Loiter', start: 20, end: 23},
  {n: '07', name: 'Lift', start: 23, end: 28},
  {n: '08', name: 'Converge', start: 28, end: 34},
  {n: '09', name: 'The run', start: 34, end: 40},
  {n: '10', name: 'Eyes on', start: 40, end: 46},
  {n: '11', name: 'The fleet', start: 46, end: 56},
  {n: '12', name: 'End card', start: 56, end: 60},
];

// VO (20 words). Start times per storyboard: 0:23, 0:42, 0:52, 0:56 + pause.
export const VO_V2: Record<string, number> = {vo1: 23.5, vo2: 42.0, vo3: 52.0, vo4: 57.1};
export const VO_V2_LEN: Record<string, number> = {vo1: 3.58, vo2: 2.53, vo3: 2.56, vo4: 0.86};
// Word offsets inside vo3 ("Cover. Sprint. Persist."), measured from the take's timestamps
export const VO3_WORDS = [0, 0.75, 1.72];

export const DISCLAIMER_V2 =
  '[PERFORMANCE DISCLAIMER: Archimedes to supply] Concept visualization. 50 nm in 30 min and hull-borne shadowing are design targets, not demonstrated performance.';
export const CONTACT_V2 = '[DEMO REQUEST · CONTACT]';
