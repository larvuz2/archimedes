import {VO_AT, VO_LEN} from './timeline';

// Music level automation (linear gain), in seconds.
// - Act 1: moderate bed, ducked under VO.
// - Under "Archimedes Freight presents... Marlin" (vo3): music almost gone.
// - Right after "Marlin": swell to full, and stay higher for the rest of Act 2/3.
const ramp = (t: number, a: number, b: number) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const smooth = (x: number) => x * x * (3 - 2 * x);

export const musicGain = (t: number): number => {
  const vo3Start = VO_AT.vo3;
  const vo3End = VO_AT.vo3 + VO_LEN.vo3;

  // Section bed level
  let bed = 0.5; // Act 1
  if (t >= 14.0) bed = 0.5 + (0.05 - 0.5) * smooth(ramp(t, 14.0, Math.min(14.6, vo3Start)));
  if (t >= vo3End - 0.1) bed = 0.05 + (1.0 - 0.05) * smooth(ramp(t, vo3End - 0.1, vo3End + 1.2));

  // Duck under the other VO lines (vo3 is already handled by the hush)
  let duck = 1;
  for (const id of Object.keys(VO_AT)) {
    if (id === 'vo3') continue;
    const s = VO_AT[id], e = s + VO_LEN[id];
    const inAmt = smooth(ramp(t, s - 0.25, s)) * (1 - smooth(ramp(t, e, e + 0.4)));
    duck = Math.min(duck, 1 - inAmt * (t > vo3End ? 0.4 : 0.35));
  }
  return bed * duck;
};
