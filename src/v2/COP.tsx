import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {
  A0, IA, IB, MEET_A, N, PARTNER_START, REACH_30MIN, RESPACE, STATION, TOI_HISTORY_START, U, USV_REACH, CUTTER_REACH,
  ease, lerpP, marlinPos, toiAt, type P,
} from './geo';

// Common operational picture. Everything is driven by absolute film time so the display is
// "the same picture" across shots 04, 05, 08 and 11. Generic look: asset types only, no real geography.
const BG = '#0D1824';
const GRID = '#172839';
const COAST_FILL = '#11283A';
const COAST_LINE = '#3C5A73';
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));

type Camera = {cx: number; cy: number; k: number};

const Plane: React.FC<{p: P; angle: number; s: number}> = ({p, angle, s}) => (
  <g transform={`translate(${p.x},${p.y}) rotate(${angle}) scale(${s})`}>
    <path d="M14 0 L-10 -3 L-12 -14 L-16 -14 L-14 -2 L-18 -1 L-18 1 L-14 2 L-16 14 L-12 14 L-10 3 Z" fill={colors.white} />
  </g>
);

const MarlinMark: React.FC<{p: P; s: number; t: number; seed: number; o: number; moving?: boolean}> = ({p, s, t, seed, o, moving}) => {
  const a = t * 1.6 + seed;
  const loopX = Math.cos(a) * 13, loopY = Math.sin(a * 2) * 6;
  return (
    <g opacity={o}>
      {!moving && (
        <ellipse cx={p.x} cy={p.y} rx={13 * s} ry={7 * s} fill="none" stroke={colors.marlin} strokeOpacity={0.45}
          strokeWidth={1.2 * s} strokeDasharray={`${2 * s} ${3 * s}`} transform={`rotate(${seed * 40} ${p.x} ${p.y})`} />
      )}
      <circle cx={p.x + (moving ? 0 : loopX * s * 0.6)} cy={p.y + (moving ? 0 : loopY * s * 0.6)} r={6.5 * s} fill={colors.marlin} />
      <circle cx={p.x + (moving ? 0 : loopX * s * 0.6)} cy={p.y + (moving ? 0 : loopY * s * 0.6)} r={10 * s} fill="none" stroke={colors.marlin} strokeOpacity={0.6} strokeWidth={1.2 * s} />
    </g>
  );
};

const Label: React.FC<{x: number; y: number; s: number; color: string; children: React.ReactNode; anchor?: 'start' | 'end' | 'middle'; size?: number; o?: number}> =
  ({x, y, s, color, children, anchor = 'start', size = 17, o = 1}) => (
    <text x={x} y={y} fill={color} fontFamily={fonts.mono} fontSize={size * s} letterSpacing={1.5 * s} textAnchor={anchor} opacity={o}
      style={{paintOrder: 'stroke'}} stroke={BG} strokeWidth={4 * s}>{children}</text>
  );

const coastPath = 'M0 940 C 220 900, 380 975, 620 935 S 1000 890, 1250 925 S 1650 965, 1920 915 L1920 1080 L0 1080 Z';

export const COP: React.FC<{start: number; camera?: (t: number) => Camera; title?: string; showReadout?: boolean}> = ({start, camera, showReadout}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const cam = camera ? camera(t) : {cx: 960, cy: 540, k: 1};
  const s = 1 / cam.k; // keeps strokes/labels constant on screen

  const toi = toiAt(t);
  // MPA orbits the contact, then breaks off for home (shot 04)
  const breakT = 12.8;
  const orbitA = (t - 10) * 1.3;
  const orbitP = {x: toi.x + Math.cos(orbitA) * 150, y: toi.y + Math.sin(orbitA) * 105};
  const homeK = ease(ramp(t, breakT, 15.6));
  const mpa = lerpP(orbitP, {x: 2050, y: -80}, homeK);
  const mpaAngle = homeK > 0 ? -38 : (orbitA * 180) / Math.PI + 90;
  const mpaVisible = t < 15.6;
  const dashed = t > breakT + 0.4; // track goes dashed when the aircraft leaves
  const coastHit = {x: toi.x + U.x * 760, y: toi.y + U.y * 760};

  // Marlins on station (shot 05+)
  const stationOn = (i: number) => ramp(t, 16.3 + ((i * 7) % 20) * 0.12, 16.6 + ((i * 7) % 20) * 0.12);
  const ringsOn = ramp(t, 17.0, 19.0);
  const marlinsShown = t >= 16.2;
  const cutter = {x: 1720, y: 175}, usv = {x: 1340, y: 450};
  const partnerK = ease(ramp(t, 47, 55));
  const partner = lerpP(PARTNER_START, {x: toi.x + 70, y: toi.y - 10}, partnerK * 0.55);

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${width / 2} ${height / 2}) scale(${cam.k}) translate(${-cam.cx} ${-cam.cy})`}>
          {/* grid */}
          {Array.from({length: 25}, (_, i) => (
            <line key={`v${i}`} x1={i * 100 - 200} y1={-300} x2={i * 100 - 200} y2={1400} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          {Array.from({length: 18}, (_, i) => (
            <line key={`h${i}`} x1={-300} y1={i * 100 - 200} x2={2300} y2={i * 100 - 200} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          {/* stylized coastline */}
          <path d={coastPath} fill={COAST_FILL} stroke={COAST_LINE} strokeWidth={2 * s} />

          {/* other assets: cutter far offshore, USV close but slow, each with a 30-min reach ring */}
          {t < 16.4 && (
            <g opacity={1 - ramp(t, 15.8, 16.4) * 0.6}>
              <circle cx={cutter.x} cy={cutter.y} r={CUTTER_REACH} fill={colors.steel} fillOpacity={0.05} stroke={colors.steel} strokeOpacity={0.7} strokeWidth={1.4 * s} strokeDasharray={`${6 * s} ${5 * s}`} />
              <path d={`M${cutter.x - 18} ${cutter.y - 7} L${cutter.x + 14} ${cutter.y - 7} L${cutter.x + 22} ${cutter.y} L${cutter.x + 14} ${cutter.y + 7} L${cutter.x - 18} ${cutter.y + 7} Z`} fill="none" stroke={colors.white} strokeWidth={2 * s} />
              <Label x={cutter.x} y={cutter.y + CUTTER_REACH + 26 * s} s={s} color={colors.steel} anchor="middle">CUTTER</Label>
              <circle cx={usv.x} cy={usv.y} r={USV_REACH} fill="none" stroke={colors.steel} strokeOpacity={0.8} strokeWidth={1.4 * s} strokeDasharray={`${4 * s} ${3 * s}`} />
              <circle cx={usv.x} cy={usv.y} r={4 * s} fill={colors.white} />
              <Label x={usv.x + 22 * s} y={usv.y + 6 * s} s={s} color={colors.steel}>USV · 3 KT</Label>
            </g>
          )}

          {/* Marlin reach rings tile the approaches */}
          {marlinsShown && STATION.map((_, i) => {
            const p = marlinPos(i, t);
            const committed = (i === IA || i === IB) && t > 46;
            return (
              <circle key={`r${i}`} cx={p.x} cy={p.y} r={REACH_30MIN} fill={colors.marlin} fillOpacity={0.035 * ringsOn * (committed ? 0.3 : 1)}
                stroke={colors.marlin} strokeOpacity={0.32 * ringsOn * stationOn(i) * (committed ? 0.35 : 1)} strokeWidth={1.3 * s} />
            );
          })}

          {/* go-fast track: history solid, projection dashed once nobody is on it */}
          <line x1={TOI_HISTORY_START.x} y1={TOI_HISTORY_START.y} x2={toi.x} y2={toi.y} stroke={colors.threat} strokeWidth={2.2 * s} strokeOpacity={0.85} />
          {dashed && t < 34 && (
            <line x1={toi.x} y1={toi.y} x2={toi.x + (coastHit.x - toi.x) * ease(ramp(t, breakT + 0.4, breakT + 1.8))}
              y2={toi.y + (coastHit.y - toi.y) * ease(ramp(t, breakT + 0.4, breakT + 1.8))}
              stroke={colors.threat} strokeWidth={2 * s} strokeDasharray={`${9 * s} ${7 * s}`} />
          )}

          {/* converge (shot 08): paths of the two committed Marlins */}
          {t > 28 && t < 46 && (
            <g>
              <line x1={A0.x} y1={A0.y} x2={marlinPos(IA, t).x} y2={marlinPos(IA, t).y} stroke={colors.marlin} strokeWidth={2.4 * s} />
              <line x1={STATION[IB].x} y1={STATION[IB].y} x2={marlinPos(IB, t).x} y2={marlinPos(IB, t).y} stroke={colors.marlin} strokeWidth={2.4 * s} />
            </g>
          )}

          {/* re-space arrows (shot 11) */}
          {t > 47 && RESPACE.map((i) => {
            const from = STATION[i], to = lerpP(from, A0, 0.38);
            const k = ease(ramp(t, 47.2, 48.2)) * (1 - ramp(t, 52, 53));
            const ang = Math.atan2(to.y - from.y, to.x - from.x);
            const tip = lerpP(from, to, 0.85);
            return (
              <g key={`ar${i}`} opacity={k}>
                <line x1={from.x} y1={from.y} x2={tip.x} y2={tip.y} stroke={colors.white} strokeWidth={2 * s} />
                <path d={`M0 0 L${-12 * s} ${-6 * s} L${-12 * s} ${6 * s} Z`} fill={colors.white} transform={`translate(${tip.x} ${tip.y}) rotate(${(ang * 180) / Math.PI})`} />
              </g>
            );
          })}

          {/* partner inbound (shot 11) */}
          {t > 46.5 && (
            <g opacity={ramp(t, 46.5, 47.5)}>
              <line x1={PARTNER_START.x} y1={PARTNER_START.y} x2={partner.x} y2={partner.y} stroke={colors.white} strokeOpacity={0.8} strokeWidth={1.8 * s} strokeDasharray={`${8 * s} ${6 * s}`} />
              <rect x={partner.x - 9 * s} y={partner.y - 9 * s} width={18 * s} height={18 * s} fill="none" stroke={colors.white} strokeWidth={2 * s} />
              <Label x={partner.x + 18 * s} y={partner.y - 16 * s} s={s} color={colors.white}>PARTNER</Label>
            </g>
          )}

          {/* Marlin markers */}
          {marlinsShown && STATION.map((_, i) => (
            <MarlinMark key={`m${i}`} p={marlinPos(i, t)} s={s} t={t} seed={i} o={stationOn(i)}
              moving={(i === IA || i === IB) && t > 28} />
          ))}
          {t > 28 && t < 46 && (
            <>
              <Label x={marlinPos(IA, t).x - 20 * s} y={marlinPos(IA, t).y + 34 * s} s={s} color={colors.marlin} anchor="end">MARLIN · HEAD-ON</Label>
              <Label x={marlinPos(IB, t).x + 20 * s} y={marlinPos(IB, t).y + 34 * s} s={s} color={colors.marlin}>MARLIN · FLANK</Label>
            </>
          )}
          {t > 18.5 && t < 21 && (
            <Label x={A0.x + 22 * s} y={A0.y - 18 * s} s={s} color={colors.marlin} o={ramp(t, 18.5, 19)}>MARLIN</Label>
          )}

          {/* go-fast contact */}
          <g transform={`translate(${toi.x} ${toi.y}) rotate(45)`}>
            <rect x={-9 * s} y={-9 * s} width={18 * s} height={18 * s} fill={colors.threat} />
          </g>
          {t < 28 || t > 46 ? (
            <>
              <Label x={toi.x - 26 * s} y={toi.y - 14 * s} s={s} color={colors.threat} anchor="end">TOI-01 · GO-FAST</Label>
              <Label x={toi.x - 26 * s} y={toi.y + 10 * s} s={s} color={colors.threat} anchor="end">NO NAV LTS · 3 POB · 30 KT</Label>
            </>
          ) : (
            <Label x={toi.x + 22 * s} y={toi.y - 14 * s} s={s} color={colors.threat}>TOI-01</Label>
          )}

          {/* patrol aircraft */}
          {mpaVisible && (
            <g>
              <Plane p={mpa} angle={mpaAngle} s={1.3 * s} />
              <Label x={mpa.x} y={mpa.y - 26 * s} s={s} color={colors.white} anchor="middle">MPA</Label>
            </g>
          )}
        </g>
      </svg>

      {/* screen-space chrome */}
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
      {cam.k < 1.2 && (
        <div style={{position: 'absolute', right: 70, bottom: 90, fontFamily: fonts.mono, fontSize: 16, color: colors.steel, textAlign: 'center'}}>
          <div style={{width: 250 / cam.k, borderBottom: `2px solid ${colors.steel}`, borderLeft: `2px solid ${colors.steel}`, borderRight: `2px solid ${colors.steel}`, height: 8}} />
          <div style={{marginTop: 6}}>50 NM</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
