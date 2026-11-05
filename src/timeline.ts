// Script v2 edit (seconds). Single source of truth for picture, VO and supers.
// VO lines + direction live in src/vo.json; audio in public/audio/vo/<id>.mp3.

export type Move = 'pushIn' | 'pullOut' | 'panLeft' | 'panRight' | 'rise' | 'still';

export type Super = {
  text: string;
  at: number; // seconds from the top
  until?: number; // defaults to shot end
  style: 'beat' | 'spec' | 'footnote' | 'label' | 'lock' | 'recap';
  x?: number; // % of width (lock box / labels)
  y?: number;
};

export type Shot = {
  id: string;
  act: 1 | 2 | 3;
  name: string;
  start: number;
  end: number;
  image?: string; // public/frames/<id>.jpg
  move: Move;
  supers?: Super[];
  sound: string;
};

export const SHOTS: Shot[] = [
  {id: 'f01', act: 1, name: 'Night sea', start: 0, end: 4, image: 'frames/f01.jpg', move: 'pushIn',
    sound: 'Wind, distant outboard whine, low synth pulse.'},
  {id: 'f02', act: 1, name: 'Operations center', start: 4, end: 7, image: 'frames/f02.jpg', move: 'pushIn',
    sound: 'Console beep.'},
  {id: 'f03', act: 1, name: 'Patrol at the pier', start: 7, end: 10.6, image: 'frames/f03.jpg', move: 'panRight',
    sound: 'Footsteps on planks, ticking starts.'},
  {id: 'f04', act: 1, name: 'Patrol in heavy chop', start: 10.6, end: 14.4, image: 'frames/f04.jpg', move: 'pullOut',
    sound: 'Hull slam, ticking builds, hard cut to silence.'},
  {id: 'f05', act: 2, name: 'Marlin wakes', start: 14.4, end: 18.6, image: 'frames/f05.jpg', move: 'pushIn',
    sound: 'Silence, beacons click on, fan spools up. Music almost gone under VO.'},
  {id: 'f06', act: 2, name: 'Marlin rises (title)', start: 18.6, end: 22.2, image: 'frames/f06.jpg', move: 'rise',
    supers: [{text: 'MARLIN', at: 18.9, style: 'beat'}],
    sound: 'Fan roar, spray. Music lifts right after "Marlin".'},
  {id: 'f07', act: 2, name: '01 Get there', start: 22.2, end: 28.4, image: 'frames/f07.jpg', move: 'panRight',
    supers: [
      {text: '01 · GET THERE', at: 22.4, style: 'label'},
      {text: 'UP TO 150 KT*', at: 25.2, style: 'spec'},
      {text: '*Design target', at: 25.2, style: 'footnote'},
    ],
    sound: 'Full fan roar, wind buffet.'},
  {id: 'f08', act: 2, name: '02 See it', start: 28.4, end: 36.4, image: 'frames/f08.jpg', move: 'still', // still so the lock box stays on the boat
    supers: [
      {text: '02 · SEE IT', at: 28.6, style: 'label'},
      {text: 'SUSPECT VESSEL · IDENTIFIED', at: 31.5, style: 'lock', x: 80, y: 32.5},
    ],
    sound: 'Soft UI tones, one lock-on chime.'},
  {id: 'f09', act: 2, name: '03 Stay on it', start: 36.4, end: 41.8, image: 'frames/f09.jpg', move: 'panRight',
    supers: [{text: '03 · STAY ON IT', at: 36.6, style: 'label'}],
    sound: 'Hull slap, wind, beacon pulse.'},
  {id: 'f10', act: 2, name: 'Partner cutter closing', start: 41.8, end: 46.4, image: 'frames/f10.jpg', move: 'pullOut',
    supers: [{text: 'TRACK SHARED → PARTNER', at: 42.2, style: 'label'}],
    sound: 'Unintelligible radio chatter, cutter engines.'},
  {id: 'f11', act: 3, name: 'Recap', start: 46.4, end: 52.6, image: 'frames/f11.jpg', move: 'pushIn',
    supers: [{text: 'GET THERE · SEE IT · STAY ON IT', at: 47.0, style: 'recap'}],
    sound: 'Three score hits on the three beats.'},
  {id: 'f12', act: 3, name: 'Hero beauty shot', start: 52.6, end: 55.4, image: 'frames/f12.jpg', move: 'panLeft',
    sound: 'Score sustains.'},
  {id: 'end', act: 3, name: 'End card', start: 55.4, end: 60, move: 'still',
    sound: 'Final hit, tail to black.'},
];

// When each VO line starts (seconds). Durations come from the audio files.
export const VO_AT: Record<string, number> = {
  vo1: 0.8, vo2: 5.6, vo3: 15.5, vo4: 22.3, vo5: 28.8, vo6: 36.7, vo7: 47.0, vo8: 55.6,
};

// Measured lengths of the current VO takes (s), used for music ducking.
export const VO_LEN: Record<string, number> = {
  vo1: 4.23, vo2: 8.7, vo3: 2.98, vo4: 5.98, vo5: 6.87, vo6: 8.41, vo7: 2.95, vo8: 2.56,
};

export const CONTACT = {name: 'Gregg Scheiferstein, CEO', email: 'gscheiferstein@archimedesfreight.com'};

export const DISCLAIMER =
  '[PLACEHOLDER: agreed concept-visualization disclaimer] Concept visualization. Performance figures are design targets, not demonstrated performance.';

export const VERSION = 'ANIMATIC v1.0';
export const TOTAL_SECONDS = 60;
