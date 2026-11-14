import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {K, tk} from './timeline';

// The tactical display for v4. One continuous world driven by film time, seen in short cuts: the contact is tagged
// (DETECT), the three nearest Marlins commit and close (ISOLATE), they box it in and hold while a partner comes
// (SURVEIL), and the rest of the fleet re-spaces (coverage). Same geometry as the approved structure PDF, x3.
// Generic look only: stylized coastline, no real geography, no named assets.
const BG = '#0D1824';
const GRID = '#172839';
const COAST_FILL = '#11283A';
const COAST_LINE = '#3C5A73';
export type P = {x: number; y: number};
export type Camera = {cx: number; cy: number; k: number};
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const out3 = (x: number) => 1 - Math.pow(1 - x, 3);
const add = (a: P, b: P, k = 1): P => ({x: a.x + b.x * k, y: a.y + b.y * k});
const lerpP = (a: P, b: P, k: number): P => ({x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k});
const dist = (a: P, b: P) => Math.hypot(a.x - b.x, a.y - b.y);

export const REACH = 222; // 50 nm in 30 min (design target) at 4.44 px per nm
const C: P = {x: 1200, y: 354}; // where the contact is first tagged
const UL = Math.hypot(-0.66, 0.75);
const U: P = {x: -0.66 / UL, y: 0.75 / UL}; // its course, toward the coast
const N: P = {x: 0.75 / UL, y: 0.66 / UL};
// the three nearest Marlins: one dead ahead on the projected track, one off each flank
const HOME: P[] = [add(C, U, 390), {x: 840, y: 330}, {x: 1320, y: 645}];
const STATIONS: P[] = [[70, 50], [190, 50], [300, 46], [520, 50], [610, 62], [130, 130], [40, 150], [560, 135], [60, 215], [180, 215], [570, 215], [120, 295],
  [240, 295], [360, 300], [480, 295], [600, 290], [630, 150], [480, 122]].map(([x, y]) => ({x: x * 3, y: y * 3}));
// the four on-station Marlins nearest the gap left by the head-on boat slide part-way into it
const RESPACE = STATIONS.map((p, i) => ({i, d: dist(p, HOME[0])})).sort((a, b) => a.d - b.d).slice(0, 4).map((o) => o.i);

export const contactAt = (t: number): P => add(C, U, 120 * clamp((t - tk(K.detect)) / (tk(K.breakdown) - tk(K.detect))) + Math.max(0, t - tk(K.breakdown)) * 2.2);
const slotAt = (i: number, t: number): P => {
  const c = contactAt(t);
  return i === 0 ? add(c, U, 114) : add(c, N, i === 1 ? -120 : 120);
};
const T_GO = tk(32); // they lift and run
const T_BOX = tk(54); // on station around the contact
export const marlinAt = (i: number, t: number): P => lerpP(HOME[i], slotAt(i, t), ease(ramp(t, T_GO, T_BOX)));
const PARTNER0: P = {x: 2150, y: 560};
export const partnerAt = (t: number): P => lerpP(PARTNER0, add(contactAt(t), {x: 170, y: 10}), 0.9 * ramp(t, tk(64), tk(84)));

const Label: React.FC<{x: number; y: number; s: number; color: string; children: React.ReactNode; anchor?: 'start' | 'end' | 'middle'; size?: number; o?: number}> =
  ({x, y, s, color, children, anchor = 'start', size = 19, o = 1}) => (
    <text x={x} y={y} fill={color} fontFamily={fonts.mono} fontSize={size * s} letterSpacing={1.6 * s} textAnchor={anchor} opacity={o}
      style={{paintOrder: 'stroke'}} stroke={BG} strokeWidth={5 * s}>{children}</text>
  );

const Arrow: React.FC<{from: P; to: P; s: number; color: string; width?: number; o?: number}> = ({from, to, s, color, width = 3, o = 1}) => {
  const ang = (Math.atan2(to.y - from.y, to.x - from.x) * 180) / Math.PI;
  if (dist(from, to) < 3 * s) return null;
  return (
    <g opacity={o}>
      <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth={width * s} strokeLinecap="round" />
      <path d={`M0 0 L${-15 * s} ${-7 * s} L${-15 * s} ${7 * s} Z`} fill={color} transform={`translate(${to.x} ${to.y}) rotate(${ang})`} />
    </g>
  );
};

const coastPath = 'M-700 1016 C 330 966, 600 1056, 960 1008 S 1500 966, 2700 1004 L2700 1500 L-700 1500 Z';

export const Map: React.FC<{start: number; camera: (t: number) => Camera; readout?: boolean}> = ({start, camera, readout}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const cam = camera(t);
  const s = 1 / cam.k; // strokes, markers and labels keep a constant size on screen

  const c = contactAt(t);
  const tDetect = tk(K.detect);
  const tagK = out3(ramp(t, tDetect, tDetect + 0.18)); // the hook brackets slam onto the contact
  const pulse = ((t - tDetect) / (60 / 104)) % 1; // one ring per beat
  const projK = ease(ramp(t, tDetect + 0.25, tDetect + 0.95)) * (1 - ramp(t, T_BOX - 0.2, T_BOX + 0.3));
  const hotOn = (i: number) => out3(ramp(t, tk(26 + i * 0.5), tk(26 + i * 0.5) + 0.16)); // the three nearest light up on the beat
  const vecOn = (i: number) => out3(ramp(t, tk(30 + i * 0.5), tk(30 + i * 0.5) + 0.22)); // their vectors draw
  const moving = t >= T_GO;
  const boxed = t >= T_BOX;
  const boxK = out3(ramp(t, T_BOX, T_BOX + 0.25));
  const boxFlash = 1 - ramp(t, T_BOX, T_BOX + 0.5);
  const cover = t >= tk(K.finale);
  const coverK = ease(ramp(t, tk(K.finale) + 0.1, tk(K.finale) + 1.3));
  const fleetO = t < tDetect ? 1 : 0.42 + 0.58 * coverK;
  const partnerO = ramp(t, tk(65.5), tk(66) + 0.15);
  const partner = partnerAt(t);
  const stationAt = (i: number): P => {
    const r = RESPACE.indexOf(i);
    return r >= 0 ? lerpP(STATIONS[i], lerpP(STATIONS[i], HOME[0], 0.34), ease(ramp(t, tk(81) + r * 0.12, tk(83.4) + r * 0.12))) : STATIONS[i];
  };
  const m = [0, 1, 2].map((i) => marlinAt(i, t));
  const slots = [0, 1, 2].map((i) => slotAt(i, t));
  const behind = add(c, U, -78);

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${width / 2} ${height / 2}) scale(${cam.k}) translate(${-cam.cx} ${-cam.cy})`}>
          {Array.from({length: 35}, (_, i) => (
            <line key={`v${i}`} x1={i * 96 - 672} y1={-700} x2={i * 96 - 672} y2={1700} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          {Array.from({length: 26}, (_, i) => (
            <line key={`h${i}`} x1={-800} y1={i * 90 - 630} x2={2800} y2={i * 90 - 630} stroke={GRID} strokeWidth={1.2 * s} />
          ))}
          <path d={coastPath} fill={COAST_FILL} stroke={COAST_LINE} strokeWidth={2 * s} />

          {/* coverage: every Marlin's 30-minute reach tiles the approaches */}
          {cover && STATIONS.map((_, i) => {
            const p = stationAt(i);
            const k = ease(ramp(t, tk(K.finale) + 0.15 + ((i * 7) % 18) * 0.035, tk(K.finale) + 0.7 + ((i * 7) % 18) * 0.035));
            return <circle key={`cr${i}`} cx={p.x} cy={p.y} r={REACH} fill={colors.marlin} fillOpacity={0.035 * k} stroke={colors.marlin} strokeOpacity={0.34 * k} strokeWidth={1.3 * s} />;
          })}
          {/* the three nearest: their reach rings show the contact is inside 30 minutes */}
          {!boxed && HOME.map((p, i) => {
            const k = hotOn(i) * (1 - 0.8 * ramp(t, T_GO - 0.1, T_GO + 0.6));
            return k > 0 ? (
              <circle key={`hr${i}`} cx={p.x} cy={p.y} r={REACH * (0.86 + 0.14 * hotOn(i))} fill={colors.marlin} fillOpacity={0.07 * k} stroke={colors.marlin} strokeOpacity={0.8 * k} strokeWidth={2 * s} />
            ) : null;
          })}

          {/* the contact's track: solid history, dashed projection on its course to the coast */}
          <line x1={C.x - U.x * 620} y1={C.y - U.y * 620} x2={c.x} y2={c.y} stroke={colors.threat} strokeWidth={2.6 * s} strokeOpacity={0.95} />
          {projK > 0 && (
            <line x1={c.x} y1={c.y} x2={c.x + U.x * 830 * projK} y2={c.y + U.y * 830 * projK} stroke={colors.threat} strokeWidth={2.2 * s}
              strokeDasharray={`${10 * s} ${8 * s}`} opacity={0.85 * Math.min(1, projK * 3)} />
          )}

          {/* ISOLATE: vectors to the three stations around where the boat will be */}
          {!boxed && [0, 1, 2].map((i) => {
            const k = vecOn(i);
            if (k <= 0) return null;
            const to = lerpP(m[i], slots[i], 0.9 * k);
            return (
              <g key={`vec${i}`}>
                {moving && <line x1={HOME[i].x} y1={HOME[i].y} x2={m[i].x} y2={m[i].y} stroke={colors.marlin} strokeOpacity={0.4} strokeWidth={1.8 * s} />}
                <Arrow from={m[i]} to={to} s={s} color={colors.marlin} />
                <circle cx={slots[i].x} cy={slots[i].y} r={11 * s} fill="none" stroke={colors.marlin} strokeWidth={2 * s} strokeDasharray={`${4.5 * s} ${3.5 * s}`} opacity={k} />
              </g>
            );
          })}
          {/* the box closes: three Marlins hold the contact between them, each with eyes on */}
          {boxed && (
            <g>
              <path d={`M ${slots[0].x} ${slots[0].y} L ${slots[1].x} ${slots[1].y} L ${behind.x} ${behind.y} L ${slots[2].x} ${slots[2].y} Z`} fill={colors.marlin}
                fillOpacity={0.1 * boxK + 0.25 * boxFlash * boxK} stroke={colors.marlin} strokeOpacity={0.75 * boxK} strokeWidth={(1.8 + 2 * boxFlash) * s}
                strokeDasharray={`${7 * s} ${5 * s}`} />
              {slots.map((p, i) => (
                <line key={`los${i}`} x1={p.x} y1={p.y} x2={c.x} y2={c.y} stroke={colors.marlin} strokeWidth={1.7 * s} strokeDasharray={`${3.5 * s} ${4.5 * s}`}
                  opacity={0.9 * ramp(t, T_BOX + 0.15 + i * 0.1, T_BOX + 0.4 + i * 0.1)} />
              ))}
            </g>
          )}

          {/* coverage: neighbours slide over to close the gap */}
          {cover && RESPACE.map((i) => {
            const from = STATIONS[i], to = lerpP(from, HOME[0], 0.34);
            const k = ease(ramp(t, tk(80.6), tk(81.4))) * (1 - ramp(t, tk(83.4), tk(84)));
            return <Arrow key={`rs${i}`} from={lerpP(from, to, 0.12)} to={lerpP(from, to, 0.94)} s={s} color={colors.white} width={2.2} o={k} />;
          })}

          {/* partner inbound */}
          {partnerO > 0 && (
            <g opacity={partnerO}>
              <line x1={PARTNER0.x + 300} y1={PARTNER0.y + 22} x2={partner.x} y2={partner.y} stroke={colors.white} strokeOpacity={0.85} strokeWidth={2 * s}
                strokeDasharray={`${9 * s} ${7 * s}`} />
              <rect x={partner.x - 10 * s} y={partner.y - 10 * s} width={20 * s} height={20 * s} fill={BG} stroke={colors.white} strokeWidth={2.4 * s} />
              <Label x={partner.x} y={partner.y + 40 * s} s={s} color={colors.white} anchor="middle">PARTNER</Label>
            </g>
          )}

          {/* the fleet on station */}
          {STATIONS.map((_, i) => {
            const p = stationAt(i);
            const th = t * 1.3 + i * 1.7;
            return (
              <g key={`st${i}`} opacity={fleetO}>
                <ellipse cx={p.x} cy={p.y} rx={21 * s} ry={10 * s} fill="none" stroke={colors.marlin} strokeOpacity={0.5} strokeWidth={1.2 * s} transform={`rotate(${i * 37} ${p.x} ${p.y})`} />
                <circle cx={p.x + Math.cos(th) * 3 * s} cy={p.y + Math.sin(th) * 2 * s} r={7 * s} fill={colors.marlin} />
              </g>
            );
          })}
          {/* the three */}
          {m.map((p, i) => {
            const hot = hotOn(i);
            const o = t < tDetect ? 1 : 0.42 + 0.58 * hot;
            return (
              <g key={`m${i}`} opacity={o}>
                <circle cx={p.x} cy={p.y} r={(7 + 3.5 * hot) * s} fill={colors.marlin} />
                {hot > 0 && <circle cx={p.x} cy={p.y} r={(19 + 14 * (1 - hot)) * s} fill="none" stroke={colors.marlin} strokeWidth={2.4 * s} opacity={hot} />}
              </g>
            );
          })}

          {/* the contact */}
          {tagK > 0 && !boxed && [0, 1].map((j) => {
            const k = (pulse + j * 0.5) % 1;
            return <circle key={`p${j}`} cx={c.x} cy={c.y} r={(26 + 70 * k) * s} fill="none" stroke={colors.threat} strokeOpacity={0.55 * (1 - k)} strokeWidth={2 * s} />;
          })}
          <g transform={`translate(${c.x} ${c.y}) rotate(45)`}>
            <rect x={-10 * s} y={-10 * s} width={20 * s} height={20 * s} fill={colors.threat} />
          </g>
          {tagK > 0 && (
            <g stroke={colors.threat} strokeWidth={3 * s} fill="none" opacity={tagK}>
              {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
                const b = (30 + (1 - tagK) * 60) * s;
                return <path key={`${sx}${sy}`} d={`M ${c.x + sx * b} ${c.y + sy * (b - 13 * s)} L ${c.x + sx * b} ${c.y + sy * b} L ${c.x + sx * (b - 13 * s)} ${c.y + sy * b}`} />;
              })}
            </g>
          )}

          {/* labels */}
          {tagK > 0 && !moving && (
            <g opacity={tagK}>
              <Label x={c.x + 46 * s} y={c.y - 18 * s} s={s} color={colors.threat} size={21}>TOI-01 · GO-FAST</Label>
              <Label x={c.x + 46 * s} y={c.y + 10 * s} s={s} color={colors.threat} size={17}>NO NAV LTS · 30 KT</Label>
            </g>
          )}
          {moving && <Label x={c.x + 30 * s} y={c.y - 22 * s} s={s} color={colors.threat}>TOI-01</Label>}
          {hotOn(2) > 0 && !moving && vecOn(0) <= 0 && (
            <Label x={HOME[0].x - 34 * s} y={HOME[0].y + 44 * s} s={s} color={colors.marlin} anchor="end" o={hotOn(2)}>NEAREST MARLINS</Label>
          )}
          {vecOn(0) > 0 && !boxed && (
            <>
              <Label x={m[0].x - 30 * s} y={m[0].y + 40 * s} s={s} color={colors.marlin} anchor="end" o={vecOn(0)}>HEAD-ON</Label>
              <Label x={m[1].x - 30 * s} y={m[1].y - 22 * s} s={s} color={colors.marlin} anchor="end" o={vecOn(1)}>FLANK</Label>
              <Label x={m[2].x + 30 * s} y={m[2].y + 36 * s} s={s} color={colors.marlin} o={vecOn(2)}>FLANK</Label>
            </>
          )}
          {boxed && !cover && (
            <Label x={slots[1].x - 12 * s} y={slots[1].y - 26 * s} s={s} color={colors.marlin} o={boxK}>{t < tk(K.surveil) ? 'ISOLATED' : 'EYES ON · LIVE'}</Label>
          )}
        </g>
      </svg>

      {/* display chrome */}
      <div style={{position: 'absolute', top: 92, left: 40, display: 'flex', gap: 14, alignItems: 'center', fontFamily: fonts.mono, fontSize: 18, color: colors.steel, letterSpacing: '0.12em'}}>
        <span style={{border: `1.5px solid ${colors.steel}`, padding: '4px 10px', borderRadius: 3}}>COP</span>
        <span style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <span style={{width: 16, height: 16, borderRadius: 8, border: `1.5px solid ${colors.marlin}`, display: 'inline-block'}} />30-MIN REACH*
        </span>
      </div>
      {readout && (
        <div style={{position: 'absolute', left: 110, bottom: 150, fontFamily: fonts.mono, color: colors.marlin, border: `2.5px solid ${colors.marlin}`, borderRadius: 4,
          padding: '14px 30px', fontSize: 64, fontWeight: 500, letterSpacing: '0.1em', background: 'rgba(8,14,22,0.72)'}}>50 NM · 30 MIN*</div>
      )}
    </AbsoluteFill>
  );
};
