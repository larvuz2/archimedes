import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {
  A0, B0, IA, IB, MEET_A, MEET_B, PARTNER_START, REACH_30MIN, RESPACE, STATION, TOI_HISTORY_START, U, USV_REACH, CUTTER_REACH,
  ease, lerpP, marlinPos, toiAt, type P,
} from './geo';
import {T} from './timeline';

// Common operational picture (COP). One continuous world driven by film time, so shots 04, 05, 08 and 11 are
// "the same display". Generic look only: asset types (MPA, CUTTER, USV, PARTNER), stylized coastline, no real geography.
const BG = '#0D1824';
const GRID = '#172839';
const COAST_FILL = '#11283A';
const COAST_LINE = '#3C5A73';
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));

export type Camera = {cx: number; cy: number; k: number};

const Plane: React.FC<{p: P; angle: number; s: number}> = ({p, angle, s}) => (
  <g transform={`translate(${p.x},${p.y}) rotate(${angle}) scale(${s})`}>
    <path d="M14 0 L-10 -3 L-12 -14 L-16 -14 L-14 -2 L-18 -1 L-18 1 L-14 2 L-16 14 L-12 14 L-10 3 Z" fill={colors.white} />
  </g>
);

// Station-keeping marker: a vessel holding station leaves a tight looping trail (generic style).
const loopPoint = (p: P, th: number, rot: number, s: number): P => {
  const lx = Math.cos(th) * 14 * s, ly = Math.sin(2 * th) * 7 * s;
  const c = Math.cos(rot), sn = Math.sin(rot);
  return {x: p.x + lx * c - ly * sn, y: p.y + lx * sn + ly * c};
};
const MarlinMark: React.FC<{p: P; s: number; t: number; seed: number; o: number; moving?: boolean; hot?: boolean}> = ({p, s, t, seed, o, moving, hot}) => {
  const rot = seed * 0.9;
  const th = t * 1.5 + seed * 1.3;
  const head = moving ? p : loopPoint(p, th, rot, s);
  const loop = Array.from({length: 33}, (_, i) => loopPoint(p, (i / 32) * Math.PI * 2, rot, s));
  const tail = Array.from({length: 12}, (_, i) => loopPoint(p, th - i * 0.16, rot, s));
  return (
    <g opacity={o}>
      {!moving && (
        <>
          <polyline points={loop.map((q) => `${q.x},${q.y}`).join(' ')} fill="none" stroke={colors.marlin} strokeOpacity={0.28} strokeWidth={1 * s} />
          <polyline points={tail.map((q) => `${q.x},${q.y}`).join(' ')} fill="none" stroke={colors.marlin} strokeOpacity={0.9} strokeWidth={1.6 * s} strokeLinecap="round" />
        </>
      )}
      <circle cx={head.x} cy={head.y} r={(hot ? 7.5 : 6) * s} fill={colors.marlin} />
      {(hot || moving) && <circle cx={head.x} cy={head.y} r={12 * s} fill="none" stroke={colors.marlin} strokeOpacity={0.7} strokeWidth={1.3 * s} />}
    </g>
  );
};

const Label: React.FC<{x: number; y: number; s: number; color: string; children: React.ReactNode; anchor?: 'start' | 'end' | 'middle'; size?: number; o?: number}> =
  ({x, y, s, color, children, anchor = 'start', size = 17, o = 1}) => (
    <text x={x} y={y} fill={color} fontFamily={fonts.mono} fontSize={size * s} letterSpacing={1.5 * s} textAnchor={anchor} opacity={o}
      style={{paintOrder: 'stroke'}} stroke={BG} strokeWidth={4 * s}>{children}</text>
  );

const Arrow: React.FC<{from: P; to: P; s: number; color: string; width?: number; o?: number}> = ({from, to, s, color, width = 2.4, o = 1}) => {
  const ang = (Math.atan2(to.y - from.y, to.x - from.x) * 180) / Math.PI;
  const len = Math.hypot(to.x - from.x, to.y - from.y);
  if (len < 2 * s) return null;
  return (
    <g opacity={o}>
      <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth={width * s} />
      <path d={`M0 0 L${-13 * s} ${-6 * s} L${-13 * s} ${6 * s} Z`} fill={color} transform={`translate(${to.x} ${to.y}) rotate(${ang})`} />
    </g>
  );
};

const coastPath = 'M-200 940 C 220 900, 380 975, 620 935 S 1000 890, 1250 925 S 1650 965, 2120 915 L2120 1280 L-200 1280 Z';
const CUTTER: P = {x: 1720, y: 175};
const USV: P = {x: 1340, y: 450};
const NEUTRAL: P = {x: 1500, y: 800}; // unlabelled neutral vessel, as in the storyboard panel

export const COP: React.FC<{start: number; camera?: (t: number) => Camera; showReadout?: boolean}> = ({start, camera, showReadout}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const cam = camera ? camera(t) : {cx: 960, cy: 540, k: 1};
  const s = 1 / cam.k; // keeps strokes and labels a constant size on screen

  const toi = toiAt(t);
  // 04: the aircraft orbits the contact, then breaks off for home
  const orbitA = (t - 10) * 1.25;
  const ORX = 120, ORY = 84;
  const orbitP = {x: toi.x + Math.cos(orbitA) * ORX, y: toi.y + Math.sin(orbitA) * ORY};
  const homeK = ease(ramp(t, T.mpaBreaks, 15.4));
  const HOME = {x: 2080, y: -60};
  const mpa = lerpP(orbitP, HOME, homeK);
  const mpaAngle = homeK > 0.02 ? (Math.atan2(HOME.y - orbitP.y, HOME.x - orbitP.x) * 180) / Math.PI : (Math.atan2(Math.cos(orbitA) * ORY, -Math.sin(orbitA) * ORX) * 180) / Math.PI;
  const mpaVisible = t < 15.4;
  const dashK = ease(ramp(t, T.trackDashed, T.trackDashed + 1.3)); // the track goes dashed, projected to the coast
  const coastHit = {x: toi.x + U.x * 760, y: toi.y + U.y * 760};

  // 05: twenty Marlins were already out there
  const order = (i: number) => (i * 7) % 20;
  const stationOn = (i: number) => ramp(t, T.fleetOn + 0.3 + order(i) * 0.12, T.fleetOn + 0.55 + order(i) * 0.12);
  const ringsOn = ease(ramp(t, T.fleetOn + 0.9, T.fleetOn + 2.6));
  const nearestOn = ease(ramp(t, T.fleetOn + 2.3, T.fleetOn + 3.0)); // the two nearest stand out
  const marlinsShown = t >= T.fleetOn + 0.2;
  const otherFade = 1 - 0.65 * ramp(t, T.fleetOn - 0.2, T.fleetOn + 0.6);
  const committed = t > 28;
  const holding = t >= 34;

  // 11: partner inbound
  const partnerK = ease(ramp(t, 46.6, 55.5));
  const partner = lerpP(PARTNER_START, {x: toi.x + 90, y: toi.y - 16}, partnerK * 0.6);

  // 08: where the two are heading
  const aNow = marlinPos(IA, t), bNow = marlinPos(IB, t);

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${width / 2} ${height / 2}) scale(${cam.k}) translate(${-cam.cx} ${-cam.cy})`}>
          {Array.from({length: 27}, (_, i) => (
            <line key={`v${i}`} x1={i * 100 - 300} y1={-400} x2={i * 100 - 300} y2={1500} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          {Array.from({length: 20}, (_, i) => (
            <line key={`h${i}`} x1={-400} y1={i * 100 - 300} x2={2400} y2={i * 100 - 300} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          <path d={coastPath} fill={COAST_FILL} stroke={COAST_LINE} strokeWidth={2 * s} />

          {/* surface assets and their 30-minute reach rings: cutter far offshore, USV close but slow */}
          <g opacity={otherFade}>
            <circle cx={CUTTER.x} cy={CUTTER.y} r={CUTTER_REACH} fill={colors.steel} fillOpacity={0.05} stroke={colors.steel} strokeOpacity={0.75}
              strokeWidth={1.4 * s} strokeDasharray={`${6 * s} ${5 * s}`} opacity={ramp(t, 10.9, 11.4)} />
            <path d={`M${CUTTER.x - 18} ${CUTTER.y - 7} L${CUTTER.x + 14} ${CUTTER.y - 7} L${CUTTER.x + 22} ${CUTTER.y} L${CUTTER.x + 14} ${CUTTER.y + 7} L${CUTTER.x - 18} ${CUTTER.y + 7} Z`}
              fill="none" stroke={colors.white} strokeWidth={2 * s} />
            <Label x={CUTTER.x} y={CUTTER.y + CUTTER_REACH + 26 * s} s={s} color={colors.steel} anchor="middle">CUTTER</Label>
            <circle cx={USV.x} cy={USV.y} r={USV_REACH} fill="none" stroke={colors.steel} strokeOpacity={0.85} strokeWidth={1.4 * s}
              strokeDasharray={`${4 * s} ${3 * s}`} opacity={ramp(t, 11.2, 11.7)} />
            <circle cx={USV.x} cy={USV.y} r={4 * s} fill={colors.white} />
            <Label x={USV.x + 22 * s} y={USV.y + 6 * s} s={s} color={colors.steel}>USV · 3 KT</Label>
            <ellipse cx={NEUTRAL.x} cy={NEUTRAL.y} rx={17 * s} ry={7.5 * s} fill="none" stroke={colors.steel} strokeOpacity={0.8} strokeWidth={1.6 * s} />
          </g>

          {/* Marlin 30-minute rings tile the approaches */}
          {marlinsShown && STATION.map((_, i) => {
            const p = marlinPos(i, t);
            const two = i === IA || i === IB;
            const hot = two && !committed ? nearestOn : 0;
            const dim = two && committed ? (holding ? 0.25 : 0.25 + 0.75 * (1 - ramp(t, 28.0, 28.6))) : 1;
            return (
              <circle key={`r${i}`} cx={p.x} cy={p.y} r={REACH_30MIN} fill={colors.marlin} fillOpacity={(0.03 + 0.05 * hot) * ringsOn * dim}
                stroke={colors.marlin} strokeOpacity={(0.3 + 0.6 * hot) * ringsOn * stationOn(i) * dim} strokeWidth={(1.2 + 1.3 * hot) * s} />
            );
          })}

          {/* go-fast track: solid history; once nobody holds it, a dashed projection on its last course to the coast */}
          <line x1={TOI_HISTORY_START.x} y1={TOI_HISTORY_START.y} x2={toi.x} y2={toi.y} stroke={colors.threat} strokeWidth={2.2 * s} strokeOpacity={0.9} />
          {dashK > 0 && t < 34 && (
            <Arrow from={toi} to={lerpP(toi, coastHit, dashK)} s={s} color={colors.threat} width={0} />
          )}
          {dashK > 0 && t < 34 && (
            <line x1={toi.x} y1={toi.y} x2={toi.x + (coastHit.x - toi.x) * dashK} y2={toi.y + (coastHit.y - toi.y) * dashK}
              stroke={colors.threat} strokeWidth={2 * s} strokeDasharray={`${9 * s} ${7 * s}`} />
          )}

          {/* 04: aircraft orbit and its track home */}
          {t < T.mpaBreaks + 0.6 && (
            <ellipse cx={toi.x} cy={toi.y} rx={ORX} ry={ORY} fill="none" stroke={colors.white} strokeOpacity={0.45 * (1 - ramp(t, T.mpaBreaks, T.mpaBreaks + 0.6))}
              strokeWidth={1.3 * s} strokeDasharray={`${5 * s} ${6 * s}`} />
          )}
          {homeK > 0 && mpaVisible && (
            <line x1={orbitP.x} y1={orbitP.y} x2={mpa.x} y2={mpa.y} stroke={colors.white} strokeOpacity={0.55} strokeWidth={1.3 * s} strokeDasharray={`${5 * s} ${6 * s}`} />
          )}

          {/* 08: the two nearest commit. Head-on straight up the projected track; the second to a point beside it */}
          {committed && t < 46 && (
            <g>
              <line x1={A0.x} y1={A0.y} x2={aNow.x} y2={aNow.y} stroke={colors.marlin} strokeOpacity={0.5} strokeWidth={1.6 * s} />
              <line x1={B0.x} y1={B0.y} x2={bNow.x} y2={bNow.y} stroke={colors.marlin} strokeOpacity={0.5} strokeWidth={1.6 * s} />
              {!holding && (
                <>
                  <Arrow from={aNow} to={lerpP(aNow, MEET_A, 0.93)} s={s} color={colors.marlin} />
                  <Arrow from={bNow} to={lerpP(bNow, MEET_B, 0.93)} s={s} color={colors.marlin} />
                  <circle cx={MEET_A.x} cy={MEET_A.y} r={11 * s} fill="none" stroke={colors.threat} strokeWidth={1.8 * s} strokeDasharray={`${4 * s} ${3 * s}`} />
                  <circle cx={MEET_B.x} cy={MEET_B.y} r={5 * s} fill="none" stroke={colors.marlin} strokeWidth={1.6 * s} />
                </>
              )}
            </g>
          )}

          {/* 11: five nearby Marlins slide over to close the gap */}
          {t > 46.8 && RESPACE.map((i) => {
            const from = STATION[i], to = lerpP(from, A0, 0.38);
            const k = ease(ramp(t, T.respace - 0.3, T.respace + 0.5)) * (1 - ramp(t, 51.2, 52.0));
            return <Arrow key={`ar${i}`} from={lerpP(from, to, 0.1)} to={lerpP(from, to, 0.92)} s={s} color={colors.white} width={2} o={k} />;
          })}

          {/* 11: partner track, inbound */}
          {t > 46.4 && (
            <g opacity={ramp(t, 46.4, 47.2)}>
              <line x1={PARTNER_START.x} y1={PARTNER_START.y} x2={partner.x} y2={partner.y} stroke={colors.white} strokeOpacity={0.85} strokeWidth={1.8 * s}
                strokeDasharray={`${8 * s} ${6 * s}`} />
              <rect x={partner.x - 9 * s} y={partner.y - 9 * s} width={18 * s} height={18 * s} fill={BG} stroke={colors.white} strokeWidth={2 * s} />
              <Label x={partner.x + 18 * s} y={partner.y - 16 * s} s={s} color={colors.white}>PARTNER</Label>
            </g>
          )}

          {/* Marlin markers */}
          {marlinsShown && STATION.map((_, i) => {
            const two = i === IA || i === IB;
            return <MarlinMark key={`m${i}`} p={marlinPos(i, t)} s={s} t={t} seed={i} o={stationOn(i)} moving={two && committed} hot={two && nearestOn > 0.5} />;
          })}
          {committed && t < 46 && (
            <>
              <Label x={aNow.x - 20 * s} y={aNow.y + 34 * s} s={s} color={colors.marlin} anchor="end">MARLIN · HEAD-ON</Label>
              <Label x={bNow.x + 20 * s} y={bNow.y + 34 * s} s={s} color={colors.marlin}>MARLIN · FLANK</Label>
            </>
          )}
          {nearestOn > 0 && !committed && (
            <Label x={(A0.x + B0.x) / 2 + 30 * s} y={(A0.y + B0.y) / 2 - 40 * s} s={s} color={colors.marlin} o={nearestOn}>MARLIN</Label>
          )}

          {/* go-fast contact */}
          <g transform={`translate(${toi.x} ${toi.y}) rotate(45)`}>
            <rect x={-9 * s} y={-9 * s} width={18 * s} height={18 * s} fill={colors.threat} />
          </g>
          {t < T.fleetOn + 0.1 || t >= 46 ? (
            <g opacity={t < 46 ? 1 - ramp(t, T.fleetOn - 0.4, T.fleetOn + 0.1) : ramp(t, 46, 46.5)}>
              <Label x={toi.x - (t < 46 ? ORX + 18 : 26 * s)} y={toi.y - 14 * s} s={s} color={colors.threat} anchor="end">TOI-01 · GO-FAST</Label>
              <Label x={toi.x - (t < 46 ? ORX + 18 : 26 * s)} y={toi.y + 10 * s} s={s} color={colors.threat} anchor="end">NO NAV LTS · 3 POB · 30 KT</Label>
            </g>
          ) : committed ? (
            <Label x={toi.x + 22 * s} y={toi.y - 14 * s} s={s} color={colors.threat}>TOI-01</Label>
          ) : null}

          {/* patrol aircraft */}
          {mpaVisible && (
            <g opacity={1 - ramp(t, 15.0, 15.4)}>
              <Plane p={mpa} angle={mpaAngle} s={1.3 * s} />
              <Label x={mpa.x} y={mpa.y - 26 * s} s={s} color={colors.white} anchor="middle">MPA</Label>
            </g>
          )}
        </g>
      </svg>

      {/* display chrome */}
      <div style={{position: 'absolute', top: 92, left: 40, display: 'flex', gap: 14, alignItems: 'center', fontFamily: fonts.mono, fontSize: 18, color: colors.steel, letterSpacing: '0.12em'}}>
        <span style={{border: `1.5px solid ${colors.steel}`, padding: '4px 10px', borderRadius: 3}}>COP</span>
        {showReadout ? (
          <span style={{border: `1.5px solid ${colors.marlin}`, color: colors.marlin, padding: '4px 14px', borderRadius: 3, fontSize: 22}}>50 NM · 30 MIN*</span>
        ) : (
          <span style={{display: 'flex', alignItems: 'center', gap: 8}}>
            <span style={{width: 16, height: 16, borderRadius: 8, border: `1.5px dashed ${colors.steel}`, display: 'inline-block'}} />30-MIN REACH
          </span>
        )}
      </div>
      {cam.k < 1.25 && (
        <div style={{position: 'absolute', right: 70, bottom: 90, fontFamily: fonts.mono, fontSize: 16, color: colors.steel, textAlign: 'center', opacity: 1 - ramp(cam.k, 1.05, 1.25)}}>
          <div style={{width: 250, borderBottom: `2px solid ${colors.steel}`, borderLeft: `2px solid ${colors.steel}`, borderRight: `2px solid ${colors.steel}`, height: 8}} />
          <div style={{marginTop: 6}}>50 NM</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
