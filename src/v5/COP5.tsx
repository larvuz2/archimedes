import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {T, tk} from './timeline';

// Common operational picture for Storyboard V7: one continuous world driven by film time, seen in shots 03, 04, 06, 08 and 13.
// 03 the gap (nothing can reach it) · 04 twenty Marlins on station, the nearest two tasked · 06 they converge, head-on and flank ·
// 08 the stop is authorized and the notional V-net profile draws itself (course-up) · 13 the boat is held, the fleet re-spaces.
// Generic look only: asset types (MPA, CUTTER, USV, PARTNER), stylized coastline, no real geography, no unit names.
const BG = '#0D1824';
const GRID = '#172839';
const COAST_FILL = '#11283A';
const COAST_LINE = '#3C5A73';
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const out3 = (x: number) => 1 - Math.pow(1 - x, 3);
export type P = {x: number; y: number};
const add = (a: P, b: P, k = 1): P => ({x: a.x + b.x * k, y: a.y + b.y * k});
const lerpP = (a: P, b: P, k: number): P => ({x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k});
const dist = (a: P, b: P) => Math.hypot(a.x - b.x, a.y - b.y);

// ---------- world (1920 x 1080 px, 5 px per nautical mile) ----------
export const REACH = 50 * 5; // Marlin: 50 nm in 30 min (design target)
const CUTTER_REACH = 12.5 * 5; // about 25 kt
const USV_REACH = 2.2 * 5; // about 3 kt (drawn a little larger so it reads)
const UL = Math.hypot(-550, 630);
export const U: P = {x: -550 / UL, y: 630 / UL}; // the go-fast's course, toward the coast
export const N: P = {x: 630 / UL, y: 550 / UL}; // right-hand normal
const TOI0: P = {x: 1243, y: 309};
const toiDist = (t: number) => 1.9 * (clamp(t, tk(16), T.foul) - tk(16));
export const toiAt = (t: number) => add(TOI0, U, toiDist(t));
const rel = (t: number, along: number, lat: number) => add(add(toiAt(t), U, along), N, lat);

// twenty Marlins on station; the two nearest the track snap to exact positions
const grid: P[] = [];
[150, 380, 610, 840].forEach((y, r) => {
  for (let i = 0; i < 5; i++) grid.push({x: (r % 2 ? 300 : 100) + i * 400, y});
});
const TT = toiAt(T.task);
const A0 = add(TT, U, REACH * 0.92); // ahead, straight down the projected track: will close head-on
const fl = Math.atan2(U.y, U.x) - (55 * Math.PI) / 180;
const B0 = add(TT, {x: Math.cos(fl), y: Math.sin(fl)}, 225); // off the flank
const nearest = (pts: P[], q: P, skip: number[]) =>
  pts.reduce((best, p, i) => (skip.includes(i) || (best >= 0 && dist(pts[best], q) < dist(p, q)) ? best : i), -1);
const IA = nearest(grid, A0, []);
const IB = nearest(grid, B0, [IA]);
grid[IA] = A0;
grid[IB] = B0;
const STATION = grid;
// coverage: five on-station Marlins nearest the two holes slide part-way in
const RESPACE = STATION.map((p, i) => ({i, d: Math.min(dist(p, A0), dist(p, B0))}))
  .filter(({i}) => i !== IA && i !== IB).sort((a, b) => a.d - b.d).slice(0, 5)
  .map(({i}) => ({i, to: lerpP(STATION[i], dist(STATION[i], A0) < dist(STATION[i], B0) ? A0 : B0, 0.36)}));

// the two tasked Marlins: converge (stepped track updates), settle at standoff, then (after the stop) hold the boat
const stepped = (t: number) => ease(clamp(T.updates.reduce((k, u) => k + clamp((t - u) / 0.45), 0) / T.updates.length));
const MEET_A = (t: number) => rel(t, 46, 0);
const MEET_B = (t: number) => rel(t, -6, 58);
const HOLD_A = (t: number) => rel(t, -26, 40); // the lead, pacing at standoff
const HOLD_B = (t: number) => rel(t, -34, -44); // the flank
const FINAL_A = (t: number) => rel(t, 34, 26); // after the pass: ahead of the stopped boat
const marlinA = (t: number): P => {
  if (t < T.updates[0]) return A0;
  if (t < tk(45)) return lerpP(A0, MEET_A(t), stepped(t));
  if (t < tk(60)) return lerpP(MEET_A(t), HOLD_A(t), ease(ramp(t, tk(45), tk(47))));
  return lerpP(HOLD_A(t), FINAL_A(t), ease(ramp(t, tk(60), tk(72))));
};
const marlinB = (t: number): P => {
  if (t < T.updates[0]) return B0;
  if (t < tk(45)) return lerpP(B0, MEET_B(t), stepped(t));
  return lerpP(MEET_B(t), HOLD_B(t), ease(ramp(t, tk(45), tk(47))));
};
const marlinPos = (i: number, t: number): P => {
  if (i === IA) return marlinA(t);
  if (i === IB) return marlinB(t);
  const r = RESPACE.find((o) => o.i === i);
  return r ? lerpP(STATION[i], r.to, ease(ramp(t, T.respace + RESPACE.indexOf(r) * 0.1, T.respace + 1.4 + RESPACE.indexOf(r) * 0.1))) : STATION[i];
};
const CUTTER: P = {x: 1720, y: 175};
const USV: P = {x: 1340, y: 450};
const NEUTRAL: P = {x: 1500, y: 800};
const PARTNER0: P = {x: 2010, y: 520};
const partnerAt = (t: number) => lerpP(PARTNER0, rel(t, 10, 110), 0.85 * ease(ramp(t, tk(80), tk(97))));

// ---------- drawing helpers ----------
export type Camera = {cx: number; cy: number; k: number; rot?: number};

const Label: React.FC<{x: number; y: number; s: number; rot: number; color: string; children: React.ReactNode; anchor?: 'start' | 'end' | 'middle'; size?: number; o?: number}> =
  ({x, y, s, rot, color, children, anchor = 'start', size = 17, o = 1}) => (
    <text x={x} y={y} fill={color} fontFamily={fonts.mono} fontSize={size * s} letterSpacing={1.5 * s} textAnchor={anchor} opacity={o}
      transform={rot ? `rotate(${-rot} ${x} ${y})` : undefined} style={{paintOrder: 'stroke'}} stroke={BG} strokeWidth={4.5 * s}>{children}</text>
  );
const Arrow: React.FC<{from: P; to: P; s: number; color: string; width?: number; o?: number; dash?: boolean}> = ({from, to, s, color, width = 2.4, o = 1, dash}) => {
  const ang = (Math.atan2(to.y - from.y, to.x - from.x) * 180) / Math.PI;
  if (dist(from, to) < 2 * s) return null;
  return (
    <g opacity={o}>
      <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth={width * s} strokeDasharray={dash ? `${8 * s} ${6 * s}` : undefined} />
      <path d={`M0 0 L${-13 * s} ${-6 * s} L${-13 * s} ${6 * s} Z`} fill={color} transform={`translate(${to.x} ${to.y}) rotate(${ang})`} />
    </g>
  );
};
const Plane: React.FC<{p: P; angle: number; s: number}> = ({p, angle, s}) => (
  <g transform={`translate(${p.x},${p.y}) rotate(${angle}) scale(${s})`}>
    <path d="M14 0 L-10 -3 L-12 -14 L-16 -14 L-14 -2 L-18 -1 L-18 1 L-14 2 L-16 14 L-12 14 L-10 3 Z" fill={colors.white} />
  </g>
);
// station-keeping marker: a tight looping trail (generic)
const loopPoint = (p: P, th: number, rot: number, s: number): P => {
  const lx = Math.cos(th) * 14 * s, ly = Math.sin(2 * th) * 7 * s;
  return {x: p.x + lx * Math.cos(rot) - ly * Math.sin(rot), y: p.y + lx * Math.sin(rot) + ly * Math.cos(rot)};
};
const MarlinMark: React.FC<{p: P; s: number; t: number; seed: number; o: number; moving?: boolean; hot?: number}> = ({p, s, t, seed, o, moving, hot = 0}) => {
  const rot = seed * 0.9, th = t * 1.5 + seed * 1.3;
  const head = moving ? p : loopPoint(p, th, rot, s);
  return (
    <g opacity={o}>
      {!moving && (
        <>
          <polyline points={Array.from({length: 33}, (_, i) => loopPoint(p, (i / 32) * Math.PI * 2, rot, s)).map((q) => `${q.x},${q.y}`).join(' ')} fill="none"
            stroke={colors.marlin} strokeOpacity={0.28} strokeWidth={1 * s} />
          <polyline points={Array.from({length: 12}, (_, i) => loopPoint(p, th - i * 0.16, rot, s)).map((q) => `${q.x},${q.y}`).join(' ')} fill="none"
            stroke={colors.marlin} strokeOpacity={0.9} strokeWidth={1.6 * s} strokeLinecap="round" />
        </>
      )}
      <circle cx={head.x} cy={head.y} r={(6 + 2 * hot) * s} fill={colors.marlin} />
      {(hot > 0 || moving) && <circle cx={head.x} cy={head.y} r={(12 + 10 * (1 - Math.max(hot, moving ? 1 : 0))) * s} fill="none" stroke={colors.marlin} strokeOpacity={0.75} strokeWidth={1.4 * s} />}
    </g>
  );
};
const coastPath = 'M-400 940 C 220 900, 380 975, 620 935 S 1000 890, 1250 925 S 1650 965, 2320 915 L2320 1480 L-400 1480 Z';
const chip = (c: string, extra: React.CSSProperties = {}): React.CSSProperties => ({fontFamily: fonts.mono, fontSize: 20, letterSpacing: '0.12em', color: c,
  border: `1.5px solid ${c}`, padding: '6px 14px', borderRadius: 3, background: 'rgba(8,14,22,0.7)', ...extra});

export const COP5: React.FC<{start: number; camera: (t: number) => Camera; readout?: boolean; stopProfile?: boolean}> = ({start, camera, readout, stopProfile}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const cam = camera(t);
  const rot = cam.rot ?? 0;
  const s = 1 / cam.k;

  const toi = toiAt(t);
  // 03: the aircraft orbits the contact, then breaks off for home; the track goes dashed, projected to the coast
  const orbitA = (t - tk(16)) * 1.3, ORX = 120, ORY = 84;
  const orbitP = {x: toi.x + Math.cos(orbitA) * ORX, y: toi.y + Math.sin(orbitA) * ORY};
  const homeK = ease(ramp(t, T.mpaBreaks, T.mpaBreaks + 2.0));
  const HOME = {x: 2080, y: -60};
  const mpa = lerpP(orbitP, HOME, homeK);
  const mpaAngle = homeK > 0.02 ? (Math.atan2(HOME.y - orbitP.y, HOME.x - orbitP.x) * 180) / Math.PI : (Math.atan2(Math.cos(orbitA) * ORY, -Math.sin(orbitA) * ORX) * 180) / Math.PI;
  const dashK = ease(ramp(t, T.trackDashed, T.trackDashed + 1.2));
  const coastHit = add(toi, U, 700);
  // 04: twenty Marlins were already out there; the nearest two are tasked
  const order = (i: number) => (i * 7) % 20;
  const stationOn = (i: number) => ramp(t, T.fleetOn + order(i) * 0.065, T.fleetOn + 0.2 + order(i) * 0.065);
  const ringsOn = ease(ramp(t, T.fleetOn + 0.6, T.fleetOn + 1.9));
  const hotK = out3(ramp(t, T.task - 0.5, T.task));
  const tasked = t >= T.task;
  const lineK = ease(ramp(t, T.intercept, T.intercept + 0.8));
  const committed = t >= T.updates[0] - 0.3;
  const otherFade = 1 - 0.6 * ramp(t, T.fleetOn - 0.3, T.fleetOn + 0.6);
  const stopped = t >= T.foul + 1.0;
  const coverK = ease(ramp(t, T.respace, T.respace + 1.4));
  const a = marlinA(t), b = marlinB(t);
  // 08: the planned pass (course frame: along U, across N)
  const planK = ease(ramp(t, T.plan, T.plan + 0.9));
  const vK = out3(ramp(t, T.plan + 0.7, T.plan + 1.0));
  const bez = (u: number) => {
    const p0 = {x: -26, y: 40}, p1 = {x: 30, y: 135}, p2 = {x: 185, y: 110}, p3 = {x: 225, y: 0};
    const m = 1 - u;
    const q = {x: m * m * m * p0.x + 3 * m * m * u * p1.x + 3 * m * u * u * p2.x + u * u * u * p3.x, y: m * m * m * p0.y + 3 * m * m * u * p1.y + 3 * m * u * u * p2.y + u * u * u * p3.y};
    return rel(t, q.x, q.y);
  };
  const apex = rel(t, 270, 0), legL = rel(t, 205, 34), legR = rel(t, 205, -34);
  const partner = partnerAt(t);
  const partnerO = ramp(t, tk(88), tk(88.5));

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${width / 2} ${height / 2}) rotate(${rot}) scale(${cam.k}) translate(${-cam.cx} ${-cam.cy})`}>
          {Array.from({length: 33}, (_, i) => <line key={`v${i}`} x1={i * 100 - 600} y1={-700} x2={i * 100 - 600} y2={1800} stroke={GRID} strokeWidth={1.2 * s} />)}
          {Array.from({length: 26}, (_, i) => <line key={`h${i}`} x1={-700} y1={i * 100 - 700} x2={2700} y2={i * 100 - 700} stroke={GRID} strokeWidth={1.2 * s} />)}
          <path d={coastPath} fill={COAST_FILL} stroke={COAST_LINE} strokeWidth={2 * s} />

          {/* today's surface assets and their 30-minute reach: the cutter far offshore, the USV close but slow */}
          <g opacity={otherFade}>
            <circle cx={CUTTER.x} cy={CUTTER.y} r={CUTTER_REACH} fill={colors.steel} fillOpacity={0.05} stroke={colors.steel} strokeOpacity={0.75}
              strokeWidth={1.4 * s} strokeDasharray={`${6 * s} ${5 * s}`} opacity={ramp(t, tk(17), tk(18))} />
            <path d={`M${CUTTER.x - 18} ${CUTTER.y - 7} L${CUTTER.x + 14} ${CUTTER.y - 7} L${CUTTER.x + 22} ${CUTTER.y} L${CUTTER.x + 14} ${CUTTER.y + 7} L${CUTTER.x - 18} ${CUTTER.y + 7} Z`}
              fill="none" stroke={colors.white} strokeWidth={2 * s} />
            <Label x={CUTTER.x} y={CUTTER.y + CUTTER_REACH + 26 * s} s={s} rot={rot} color={colors.steel} anchor="middle">CUTTER</Label>
            <circle cx={USV.x} cy={USV.y} r={USV_REACH} fill="none" stroke={colors.steel} strokeOpacity={0.85} strokeWidth={1.4 * s} strokeDasharray={`${4 * s} ${3 * s}`}
              opacity={ramp(t, tk(17.5), tk(18.5))} />
            <circle cx={USV.x} cy={USV.y} r={4 * s} fill={colors.white} />
            <Label x={USV.x + 22 * s} y={USV.y + 6 * s} s={s} rot={rot} color={colors.steel}>USV · 3 KT</Label>
            <ellipse cx={NEUTRAL.x} cy={NEUTRAL.y} rx={17 * s} ry={7.5 * s} fill="none" stroke={colors.steel} strokeOpacity={0.8} strokeWidth={1.6 * s} />
          </g>

          {/* Marlin 30-minute rings tile the approaches */}
          {t >= T.fleetOn && STATION.map((_, i) => {
            const p = marlinPos(i, t);
            const two = i === IA || i === IB;
            const hot = two ? hotK * (1 - ramp(t, tk(38), tk(39))) : 0;
            const dim = two && committed ? 0.2 : 1;
            return (
              <circle key={`r${i}`} cx={p.x} cy={p.y} r={REACH} fill={colors.marlin} fillOpacity={(0.03 + 0.06 * hot) * ringsOn * dim}
                stroke={colors.marlin} strokeOpacity={(0.3 + 0.6 * hot) * ringsOn * stationOn(i) * dim + 0.12 * coverK * (two ? 0 : 1)} strokeWidth={(1.2 + 1.4 * hot) * s} />
            );
          })}

          {/* go-fast track: solid history; once nobody can reach it, a dashed projection on its last course to the coast */}
          <line x1={TOI0.x - U.x * 420} y1={TOI0.y - U.y * 420} x2={toi.x} y2={toi.y} stroke={colors.threat} strokeWidth={2.2 * s} strokeOpacity={0.9} />
          {dashK > 0 && !stopped && (
            <line x1={toi.x} y1={toi.y} x2={toi.x + (coastHit.x - toi.x) * dashK} y2={toi.y + (coastHit.y - toi.y) * dashK} stroke={colors.threat}
              strokeWidth={2 * s} strokeDasharray={`${9 * s} ${7 * s}`} opacity={stopProfile ? 0.5 : 1} />
          )}

          {/* 03: aircraft orbit and its track home */}
          {t < T.mpaBreaks + 0.6 && (
            <ellipse cx={toi.x} cy={toi.y} rx={ORX} ry={ORY} fill="none" stroke={colors.white} strokeOpacity={0.45 * (1 - ramp(t, T.mpaBreaks, T.mpaBreaks + 0.6))}
              strokeWidth={1.3 * s} strokeDasharray={`${5 * s} ${6 * s}`} />
          )}
          {homeK > 0 && t < T.mpaBreaks + 2.0 && (
            <line x1={orbitP.x} y1={orbitP.y} x2={mpa.x} y2={mpa.y} stroke={colors.white} strokeOpacity={0.55} strokeWidth={1.3 * s} strokeDasharray={`${5 * s} ${6 * s}`} />
          )}

          {/* 04: intercept lines from the two tasked Marlins to the track */}
          {tasked && t < tk(38) && lineK > 0 && (
            <>
              <Arrow from={A0} to={lerpP(A0, MEET_A(t), 0.94 * lineK)} s={s} color={colors.marlin} width={2} dash />
              <Arrow from={B0} to={lerpP(B0, MEET_B(t), 0.94 * lineK)} s={s} color={colors.marlin} width={2} dash />
            </>
          )}
          {/* 06: they close: head-on straight up the projected track, the second from the flank */}
          {committed && t < tk(45) && (
            <g>
              <line x1={A0.x} y1={A0.y} x2={a.x} y2={a.y} stroke={colors.marlin} strokeOpacity={0.5} strokeWidth={1.6 * s} />
              <line x1={B0.x} y1={B0.y} x2={b.x} y2={b.y} stroke={colors.marlin} strokeOpacity={0.5} strokeWidth={1.6 * s} />
              <Arrow from={a} to={lerpP(a, MEET_A(t), 0.9)} s={s} color={colors.marlin} />
              <Arrow from={b} to={lerpP(b, MEET_B(t), 0.9)} s={s} color={colors.marlin} />
            </g>
          )}

          {/* 08: the notional stop profile: the lead's pass path swings wide around the boat and back onto its track well ahead; the V on the track, open toward the boat */}
          {stopProfile && planK > 0 && (
            <g>
              <polyline points={Array.from({length: 41}, (_, i) => bez((i / 40) * planK)).map((q) => `${q.x},${q.y}`).join(' ')} fill="none" stroke={colors.marlin}
                strokeWidth={2.4 * s} strokeDasharray={`${8 * s} ${6 * s}`} />
              {planK > 0.97 && <Arrow from={bez(0.96)} to={bez(1.0)} s={s} color={colors.marlin} />}
              <g opacity={vK}>
                <polyline points={`${legL.x},${legL.y} ${apex.x},${apex.y} ${legR.x},${legR.y}`} fill="none" stroke={colors.white} strokeWidth={2.6 * s}
                  strokeDasharray={`${3 * s} ${4 * s}`} />
                <Label x={apex.x} y={apex.y} s={s} rot={rot} color={colors.white} size={18}>{'  V-NET'}</Label>
              </g>
            </g>
          )}

          {/* coverage: neighbours slide over to close the two holes */}
          {t > T.respace - 0.2 && RESPACE.map(({i, to}) => (
            <Arrow key={`rs${i}`} from={lerpP(STATION[i], to, 0.12)} to={lerpP(STATION[i], to, 0.94)} s={s} color={colors.white} width={2}
              o={ease(ramp(t, T.respace - 0.2, T.respace + 0.4)) * (1 - ramp(t, T.respace + 2.4, T.respace + 3.0))} />
          ))}

          {/* partner inbound */}
          {partnerO > 0 && (
            <g opacity={partnerO}>
              <line x1={PARTNER0.x + 200} y1={PARTNER0.y + 10} x2={partner.x} y2={partner.y} stroke={colors.white} strokeOpacity={0.85} strokeWidth={1.8 * s} strokeDasharray={`${8 * s} ${6 * s}`} />
              <rect x={partner.x - 9 * s} y={partner.y - 9 * s} width={18 * s} height={18 * s} fill={BG} stroke={colors.white} strokeWidth={2 * s} />
              <Label x={partner.x + 18 * s} y={partner.y - 16 * s} s={s} rot={rot} color={colors.white}>PARTNER</Label>
            </g>
          )}

          {/* Marlin markers */}
          {t >= T.fleetOn && STATION.map((_, i) => {
            const two = i === IA || i === IB;
            return <MarlinMark key={`m${i}`} p={marlinPos(i, t)} s={s} t={t} seed={i} o={stationOn(i)} moving={two && committed} hot={two ? hotK : 0} />;
          })}
          {tasked && t < tk(38) && (
            <g opacity={out3(ramp(t, T.task + 0.15, T.task + 0.4))}>
              <Label x={A0.x + 18 * s} y={A0.y - 18 * s} s={s} rot={rot} color={colors.white} size={19}>TASKED</Label>
              <Label x={B0.x + 18 * s} y={B0.y - 18 * s} s={s} rot={rot} color={colors.white} size={19}>TASKED</Label>
            </g>
          )}
          {committed && t < tk(45) && (
            <>
              <Label x={a.x - 20 * s} y={a.y + 34 * s} s={s} rot={rot} color={colors.marlin} anchor="end">MARLIN · HEAD-ON</Label>
              <Label x={b.x + 20 * s} y={b.y + 34 * s} s={s} rot={rot} color={colors.marlin}>MARLIN · FLANK</Label>
            </>
          )}
          {stopProfile && (
            <>
              <Label x={a.x} y={a.y - 22 * s} s={s} rot={rot} color={colors.marlin} anchor="middle">LEAD</Label>
              <Label x={b.x} y={b.y + 34 * s} s={s} rot={rot} color={colors.marlin} anchor="middle">FLANK</Label>
            </>
          )}

          {/* the go-fast */}
          <g transform={`translate(${toi.x} ${toi.y}) rotate(45)`}>
            <rect x={-9 * s} y={-9 * s} width={18 * s} height={18 * s} fill={colors.threat} />
          </g>
          {t < T.fleetOn ? (
            <g opacity={1 - ramp(t, T.fleetOn - 0.5, T.fleetOn)}>
              <Label x={toi.x - ORX - 18} y={toi.y - 14 * s} s={s} rot={rot} color={colors.threat} anchor="end">TOI-01 · GO-FAST</Label>
              <Label x={toi.x - ORX - 18} y={toi.y + 10 * s} s={s} rot={rot} color={colors.threat} anchor="end">NO NAV LTS · 3 POB · 30 KT</Label>
            </g>
          ) : (
            <Label x={toi.x + 22 * s} y={toi.y - 14 * s} s={s} rot={rot} color={colors.threat}>{stopped ? 'TOI-01 · DIW' : 'TOI-01'}</Label>
          )}

          {/* patrol aircraft */}
          {t < T.mpaBreaks + 2.0 && (
            <g opacity={1 - ramp(t, T.mpaBreaks + 1.6, T.mpaBreaks + 2.0)}>
              <Plane p={mpa} angle={mpaAngle} s={1.3 * s} />
              <Label x={mpa.x} y={mpa.y - 26 * s} s={s} rot={rot} color={colors.white} anchor="middle">MPA</Label>
            </g>
          )}
        </g>
      </svg>

      {/* display chrome */}
      <div style={{position: 'absolute', top: 92, left: 40, display: 'flex', gap: 14, alignItems: 'center', fontFamily: fonts.mono, fontSize: 18, color: colors.steel, letterSpacing: '0.12em'}}>
        <span style={{border: `1.5px solid ${colors.steel}`, padding: '4px 10px', borderRadius: 3}}>COP</span>
        <span style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <span style={{width: 16, height: 16, borderRadius: 8, border: `1.5px dashed ${colors.steel}`, display: 'inline-block'}} />30-MIN REACH
        </span>
        {tasked && t < tk(38) && <span style={chip(colors.white, {opacity: out3(ramp(t, T.task, T.task + 0.2))})}>C2 · TASK MARLIN ×2</span>}
      </div>
      {readout && (
        <>
          <div style={chip(colors.marlin, {position: 'absolute', top: 150, left: 40, fontSize: 40, padding: '10px 24px', borderWidth: 2.5})}>50 NM · 30 MIN*</div>
          <div style={{position: 'absolute', left: 40, top: 232, fontFamily: fonts.mono, fontSize: 20, color: 'rgba(255,255,255,0.85)'}}>*Design target</div>
        </>
      )}
      {stopProfile && (
        <div style={{position: 'absolute', top: 150, right: 64, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10, opacity: out3(ramp(t, T.authorized, T.authorized + 0.2))}}>
          <div style={chip(colors.white, {fontSize: 24, padding: '8px 18px'})}>C2 · STOP AUTHORIZED · PROFILE: V-NET</div>
          <div style={{fontFamily: fonts.mono, fontSize: 20, letterSpacing: '0.14em', color: colors.steel}}>NOTIONAL STOP PROFILE</div>
        </div>
      )}
      {cam.k < 1.25 && (
        <div style={{position: 'absolute', right: 70, bottom: 90, fontFamily: fonts.mono, fontSize: 16, color: colors.steel, textAlign: 'center', opacity: 1 - ramp(cam.k, 1.05, 1.25)}}>
          <div style={{width: 250, borderBottom: `2px solid ${colors.steel}`, borderLeft: `2px solid ${colors.steel}`, borderRight: `2px solid ${colors.steel}`, height: 8}} />
          <div style={{marginTop: 6}}>50 NM</div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------- cameras for the display shots (film time in seconds) ----------
const smooth = (x: number) => x * x * (3 - 2 * x);
const UANG = (Math.atan2(U.y, U.x) * 180) / Math.PI;
// 03: pull back from the contact to the whole picture
export const cam03 = (t: number): Camera => {
  const k = 1 - smooth(ramp(t, tk(16), tk(18.5)));
  const c = toiAt(t);
  return {cx: 960 + (c.x - 960) * k, cy: 540 + (c.y - 540) * k, k: 1 + 1.6 * k};
};
// 04: the same picture; a slow push toward the two that get tasked
export const cam04 = (t: number): Camera => {
  const k = smooth(ramp(t, T.task - 0.5, tk(32)));
  const c = lerpP(A0, B0, 0.5);
  return {cx: 960 + (c.x - 960) * 0.35 * k, cy: 540 + (c.y - 540) * 0.35 * k, k: 1 + 0.18 * k};
};
// 06: tight on the two closing tracks
export const cam06 = (t: number): Camera => {
  const c = lerpP(lerpP(toiAt(t), A0, 0.45), B0, 0.18);
  return {cx: c.x, cy: c.y, k: 1.85 + 0.2 * ramp(t, tk(38), tk(45))};
};
// 08: course-up and tight: the plan reads left to right, the boat heading right
export const cam08 = (t: number): Camera => {
  const c = rel(t, 105, 18);
  return {cx: c.x, cy: c.y, k: 2.35 + 0.12 * ramp(t, tk(54), tk(60)), rot: -UANG};
};
// 13: pull back from the held boat to the whole picture, framed like 03
export const cam13 = (t: number): Camera => {
  const k = 1 - smooth(ramp(t, tk(88), tk(90.5)));
  const c = toiAt(t);
  return {cx: 960 + (c.x - 960) * k, cy: 540 + (c.y - 540) * k, k: 1 + 1.3 * k};
};
