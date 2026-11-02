// Shot timing locked to Storyboard V3 (seconds). Edit here only.
export type Shot = {
  id: number;
  name: string;
  act: 1 | 2 | 3;
  start: number;
  end: number;
  vo: string;
  onScreen: string;
  sound: string;
};

export const SHOTS: Shot[] = [
  {id: 1, act: 1, name: 'Wide aerial, slow push', start: 0, end: 5,
    vo: "Every day, America's ports carry the cargo our economy and our military depend on.",
    onScreen: 'Over 80% of global trade by volume moves by sea. (Source: UNCTAD)',
    sound: 'Gulls, distant crane horns. Low synth pulse fades in.'},
  {id: 2, act: 1, name: 'Console insert, then water', start: 5, end: 10,
    vo: 'The threats are small, fast, and often dark: hostile craft in the harbor, smugglers on the approaches.',
    onScreen: 'NO AIS · INBOUND · NO AIS',
    sound: 'Console beep; outboard whine passes left to right.'},
  {id: 3, act: 1, name: 'Pier, clock overlay', start: 10, end: 14,
    vo: "Conventional patrols take time to respond, and rough water slows them further. Threats don't wait.",
    onScreen: '(none — clock carries it)',
    sound: 'Ticking builds, then cuts to silence on the last frame.'},
  {id: 4, act: 2, name: 'Low-angle reveal', start: 14, end: 18,
    vo: 'Archimedes Freight presents Marlin.',
    onScreen: 'ARCHIMEDES logo · MARLIN',
    sound: 'Engine spools up; score lifts on the cut.'},
  {id: 5, act: 2, name: 'Tracking shot + reach map', start: 18, end: 24,
    vo: 'Under 24 feet. Flying on foils at up to 150 knots. Harbor to approaches in minutes, even through open-water chop.',
    onScreen: 'HYDROFOIL · <24 FT · UP TO 150 KT* · HIGH-SPEED OPS TO SEA STATE 3*  (*Design target)',
    sound: 'Full engine roar, wind buffet on the mic.'},
  {id: 6, act: 2, name: 'Mission 1: harbor', start: 24, end: 32,
    vo: 'In the harbor, its sensors find what fixed cameras miss, and put eyes on it fast.',
    onScreen: 'MISSION 1 · PORT SECURITY',
    sound: 'Engine ducks under soft UI tones; one lock-on chime.'},
  {id: 7, act: 2, name: 'Mission 2: counter-drug', start: 32, end: 41,
    vo: 'Offshore, it flies over the chop that slows smugglers down, and shadows them until a boarding team arrives.',
    onScreen: 'MISSION 2 · COUNTER-DRUG',
    sound: 'Wind, hull slap from the go-fast, distant radio chatter (unintelligible).'},
  {id: 8, act: 2, name: 'Split-screen payoff', start: 41, end: 45,
    vo: 'Detect. Close. Identify. Hand off.',
    onScreen: 'DETECT · CLOSE · IDENTIFY · HAND OFF',
    sound: 'Four hits in the score land on the four words.'},
  {id: 9, act: 3, name: 'Animated map pull-back', start: 45, end: 51,
    vo: 'As a networked picket, Marlin extends the reach of every partner, from pier to approach.',
    onScreen: 'PORT OPS · PARTNERS',
    sound: 'Score broadens and resolves; engine fades out.'},
  {id: 10, act: 3, name: 'Callback to shot 1', start: 51, end: 56,
    vo: 'Ports stay open. Cargo keeps moving. Contraband stays out.',
    onScreen: '(none)',
    sound: 'Port ambience from shot 1 returns under the score.'},
  {id: 11, act: 3, name: 'End card', start: 56, end: 60,
    vo: 'Marlin. Speed is security.',
    onScreen: 'ARCHIMEDES · MARLIN · Speed is security. · Gregg Scheiferstein, CEO · gscheiferstein@archimedesfreight.com · [disclaimer]',
    sound: 'Final score hit, then a single engine rev to black.'},
];

export const DISCLAIMER =
  '[PLACEHOLDER — agreed concept-visualization disclaimer from Archimedes] Concept visualization. Performance figures are design targets, not demonstrated performance.';

export const TOTAL_SECONDS = 60;
