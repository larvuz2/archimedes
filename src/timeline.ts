// Shot timing (seconds). Edit here only.
// Retimed from Storyboard V3 so the VO fits: Act 1 runs 0-17.5s (was 0-14s), the missions
// give back the time; Act 3 is unchanged. Original times are in the comment on each shot.
export type Shot = {
  id: number;
  name: string;
  act: 1 | 2 | 3;
  start: number;
  end: number;
  /** When the VO line starts, in seconds from the top (may lead the cut slightly). */
  voAt: number;
  vo: string;
  onScreen: string;
  sound: string;
  /** Storyboard sketch in public/storyboard (composition reference). */
  sketch: string;
};

export const SHOTS: Shot[] = [
  {id: 1, sketch: 'storyboard/shot-01.png', act: 1, name: 'Wide aerial, slow push', start: 0, end: 5, voAt: 0.5, // storyboard V3: 0-5s
    vo: "Every day, America's ports carry the cargo our economy and our military depend on.",
    onScreen: 'Over 80% of global trade by volume moves by sea. (Source: UNCTAD)',
    sound: 'Gulls, distant crane horns. Low synth pulse fades in.'},
  {id: 2, sketch: 'storyboard/shot-02.png', act: 1, name: 'Console insert, then water', start: 5, end: 11.5, voAt: 4.9, // storyboard V3: 5-10s
    vo: 'The threats are small, fast, and often dark: hostile craft in the harbor, smugglers on the approaches.',
    onScreen: 'NO AIS · INBOUND · NO AIS',
    sound: 'Console beep; outboard whine passes left to right.'},
  {id: 3, sketch: 'storyboard/shot-03.png', act: 1, name: 'Pier, clock overlay', start: 11.5, end: 17.5, voAt: 11.7, // storyboard V3: 10-14s
    vo: "Conventional patrols take time to respond, and rough water slows them further. Threats don't wait.",
    onScreen: '(none — clock carries it)',
    sound: 'Ticking builds, then cuts to silence on the last frame.'},
  {id: 4, sketch: 'storyboard/shot-04.png', act: 2, name: 'Low-angle reveal', start: 17.5, end: 21.5, voAt: 19.2, // storyboard V3: 14-18s
    vo: 'Archimedes Freight presents Marlin.',
    onScreen: 'ARCHIMEDES logo · MARLIN',
    sound: 'Engine spools up; score lifts on the cut.'},
  {id: 5, sketch: 'storyboard/shot-05.png', act: 2, name: 'Tracking shot + reach map', start: 21.5, end: 28.5, voAt: 21.4, // storyboard V3: 18-24s
    vo: 'Under 24 feet. Flying on foils at up to 150 knots. Harbor to approaches in minutes, even through open-water chop.',
    onScreen: 'HYDROFOIL · <24 FT · UP TO 150 KT* · HIGH-SPEED OPS TO SEA STATE 3*  (*Design target)',
    sound: 'Full engine roar, wind buffet on the mic.'},
  {id: 6, sketch: 'storyboard/shot-06.png', act: 2, name: 'Mission 1: harbor', start: 28.5, end: 34.5, voAt: 29.4, // storyboard V3: 24-32s
    vo: 'In the harbor, its sensors find what fixed cameras miss, and put eyes on it fast.',
    onScreen: 'MISSION 1 · PORT SECURITY',
    sound: 'Engine ducks under soft UI tones; one lock-on chime.'},
  {id: 7, sketch: 'storyboard/shot-07.png', act: 2, name: 'Mission 2: counter-drug', start: 34.5, end: 41, voAt: 34.9, // storyboard V3: 32-41s
    vo: 'Offshore, it flies over the chop that slows smugglers down, and shadows them until a boarding team arrives.',
    onScreen: 'MISSION 2 · COUNTER-DRUG',
    sound: 'Wind, hull slap from the go-fast, distant radio chatter (unintelligible).'},
  {id: 8, sketch: 'storyboard/shot-08.png', act: 2, name: 'Split-screen payoff', start: 41, end: 45, voAt: 41.2, // storyboard V3: 41-45s
    vo: 'Detect. Close. Identify. Hand off.',
    onScreen: 'DETECT · CLOSE · IDENTIFY · HAND OFF',
    sound: 'Four hits in the score land on the four words.'},
  {id: 9, sketch: 'storyboard/shot-09.png', act: 3, name: 'Animated map pull-back', start: 45, end: 51, voAt: 45.6, // storyboard V3: 45-51s
    vo: 'As a networked picket, Marlin extends the reach of every partner, from pier to approach.',
    onScreen: 'PORT OPS · PARTNERS',
    sound: 'Score broadens and resolves; engine fades out.'},
  {id: 10, sketch: 'storyboard/shot-10.png', act: 3, name: 'Callback to shot 1', start: 51, end: 56, voAt: 51.6, // storyboard V3: 51-56s
    vo: 'Ports stay open. Cargo keeps moving. Contraband stays out.',
    onScreen: '(none)',
    sound: 'Port ambience from shot 1 returns under the score.'},
  {id: 11, sketch: 'storyboard/shot-11.png', act: 3, name: 'End card', start: 56, end: 60, voAt: 56.6, // storyboard V3: 56-60s
    vo: 'Marlin. Speed is security.',
    onScreen: 'ARCHIMEDES · MARLIN · Speed is security. · Gregg Scheiferstein, CEO · gscheiferstein@archimedesfreight.com · [disclaimer]',
    sound: 'Final score hit, then a single engine rev to black.'},
];

export const DISCLAIMER =
  '[PLACEHOLDER — agreed concept-visualization disclaimer from Archimedes] Concept visualization. Performance figures are design targets, not demonstrated performance.';

export const TOTAL_SECONDS = 60;
