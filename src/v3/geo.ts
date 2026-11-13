// v3 tactical display geometry (world = 1920x1080 px, 5 px per nautical mile).
// All positions are functions of absolute film time t (seconds) so shots 04/05/08/11 share one world.
export type P = {x: number; y: number};
export const PX_PER_NM = 5;
export const REACH_30MIN = 50 * PX_PER_NM; // Marlin: 50 nm in 30 min (design target)
export const CUTTER_REACH = 12.5 * PX_PER_NM; // ~25 kt
export const USV_REACH = 2.2 * PX_PER_NM; // ~3 kt (drawn slightly larger so it reads)

const add = (a: P, b: P, k = 1): P => ({x: a.x + b.x * k, y: a.y + b.y * k});
export const lerpP = (a: P, b: P, k: number): P => ({x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k});
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

// Go-fast course: toward the coast (down-left)
const L = Math.hypot(-550, 630);
export const U: P = {x: -550 / L, y: 630 / L};
export const N: P = {x: 630 / L, y: 550 / L}; // right-hand normal (flank side)
export const TOI0: P = {x: 1243, y: 309};

const toiDist = (t: number) => {
  if (t < 10) return 0;
  if (t < 16) return (t - 10) * 5.8;
  if (t < 28) return 35 + (t - 16) * 1.0;
  if (t < 34) return 47 + (t - 28) * 4;
  return 71 + (t - 34) * 0.5;
};
export const toiAt = (t: number) => add(TOI0, U, toiDist(t));
export const TOI_HISTORY_START = add(TOI0, U, -420);

// Marlins: hex grid of 20 on station, the two nearest the track snapped to exact positions.
const T16 = toiAt(16);
export const A0: P = add(T16, U, REACH_30MIN * 0.98); // head-on, straight down the projected track
const flankDir = (() => {
  const a = Math.atan2(U.y, U.x) - (55 * Math.PI) / 180;
  return {x: Math.cos(a), y: Math.sin(a)};
})();
export const B0: P = add(T16, flankDir, 240); // off the flank, inside 30-min reach

const grid: P[] = [];
[150, 380, 610, 840].forEach((y, r) => {
  for (let i = 0; i < 5; i++) grid.push({x: (r % 2 ? 300 : 100) + i * 400, y});
});
const nearest = (pts: P[], q: P, skip: number[]) =>
  pts.reduce((best, p, i) => (skip.includes(i) || (best >= 0 && Math.hypot(pts[best].x - q.x, pts[best].y - q.y) < Math.hypot(p.x - q.x, p.y - q.y)) ? best : i), -1);
export const IA = nearest(grid, A0, []);
export const IB = nearest(grid, B0, [IA]);
grid[IA] = A0;
grid[IB] = B0;
export const STATION = grid;

// Re-space (shot 11): five nearest neighbours of A's old station slide part-way into the gap.
export const RESPACE = STATION.map((p, i) => ({p, i}))
  .filter(({i}) => i !== IA && i !== IB)
  .sort((a, b) => Math.hypot(a.p.x - A0.x, a.p.y - A0.y) - Math.hypot(b.p.x - A0.x, b.p.y - A0.y))
  .slice(0, 5)
  .map(({i}) => i);

// Converge (shot 08): stepped track updates every 1.5 s, eased.
export const UPDATES = [28.6, 30.1, 31.6, 33.1];
const stepped = (t: number) => {
  let k = 0;
  UPDATES.forEach((u) => (k += clamp((t - u) / 0.6)));
  return ease(clamp(k / UPDATES.length));
};
export const MEET_A = add(toiAt(34), U, 45); // just ahead of the boat, at standoff
export const MEET_B = add(toiAt(34), N, 55); // beside the track

// Holding positions while shadowing (shot 11)
export const holdA = (t: number) => add(toiAt(t), U, 45);
export const holdB = (t: number) => add(toiAt(t), N, 55);

export const marlinPos = (i: number, t: number): P => {
  const base = STATION[i];
  if (i === IA) return t < 34 ? lerpP(A0, MEET_A, stepped(t)) : holdA(t);
  if (i === IB) return t < 34 ? lerpP(B0, MEET_B, stepped(t)) : holdB(t);
  const r = RESPACE.indexOf(i);
  if (r >= 0 && t > 47) {
    const k = ease(clamp((t - 47.4 - r * 0.25) / 2.2));
    return lerpP(base, lerpP(base, A0, 0.38), k);
  }
  return base;
};

export const PARTNER_START: P = {x: 2000, y: 470};
