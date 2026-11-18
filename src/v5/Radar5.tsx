import React from 'react';
import {AbsoluteFill, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {T} from './timeline';

// 02 · Detected and designated (Storyboard V7). The patrol aircraft's radar: an intelligence cue has put it over a search
// box; one return inside the box holds sweep after sweep; the operator hooks it, and the cue is confirmed: detected, and
// designated TOI-01, a suspect go-fast. All of this is the existing enterprise's work, not Marlin's.
// Generic depiction only (no model, band or performance). Intel appears only as a cue box.
const O = {x: 960, y: 1060}; // own aircraft
const BG = '#0B1520';
const CONTACT = {x: 1105, y: 455};
const BEARING = (Math.atan2(CONTACT.y - O.y, CONTACT.x - O.x) * 180) / Math.PI;
const HALF = 30; // sector half-width (deg)
const PERIOD = 0.75; // the sweep crosses the contact every 0.75 s
const AOI = {cx: CONTACT.x - 20, cy: CONTACT.y + 5, w: 500, h: 250, rot: -12};

// sweep bearing over time: a sector scan that crosses the contact's bearing at every T.radarPasses
const sweepAt = (t: number) => BEARING + HALF * (2 / Math.PI) * Math.asin(Math.sin((Math.PI * (t - T.radarPasses[0])) / PERIOD));
// time since the sweep last crossed a given bearing (searching back one full scan)
const ageOf = (bearing: number, t: number) => {
  let prev = sweepAt(t);
  for (let i = 1; i <= 90; i++) {
    const tt = t - (i * 2 * PERIOD) / 90;
    const cur = sweepAt(tt);
    if ((prev - bearing) * (cur - bearing) <= 0) return (i * 2 * PERIOD) / 90;
    prev = cur;
  }
  return 99;
};

const inAoi = (x: number, y: number) => {
  const a = (-AOI.rot * Math.PI) / 180;
  const dx = x - AOI.cx, dy = y - AOI.cy;
  const u = dx * Math.cos(a) - dy * Math.sin(a), v = dx * Math.sin(a) + dy * Math.cos(a);
  return Math.abs(u) < AOI.w / 2 && Math.abs(v) < AOI.h / 2;
};

// sea clutter: dense inside the search box (where the radar is looking), sparse close to the aircraft
const CLUTTER = Array.from({length: 900}, (_, i) => {
  const inside = i < 620;
  let x: number, y: number;
  if (inside) {
    const u = (random(`cu${i}`) - 0.5) * AOI.w, v = (random(`cv${i}`) - 0.5) * AOI.h;
    const a = (AOI.rot * Math.PI) / 180;
    x = AOI.cx + u * Math.cos(a) - v * Math.sin(a);
    y = AOI.cy + u * Math.sin(a) + v * Math.cos(a);
  } else {
    const r = 40 + Math.pow(random(`cr${i}`), 1.6) * 330;
    const a = ((BEARING + (random(`ca${i}`) - 0.5) * 2 * HALF * 1.1) * Math.PI) / 180;
    x = O.x + Math.cos(a) * r;
    y = O.y + Math.sin(a) * r;
  }
  return {x, y, i, bearing: (Math.atan2(y - O.y, x - O.x) * 180) / Math.PI, size: 1.2 + random(`cs${i}`) * 2.0};
});

export const Radar5: React.FC<{start: number}> = ({start}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const sweep = sweepAt(t);
  const sr = (sweep * Math.PI) / 180;
  const scanNo = (age: number) => Math.floor((t - age - T.radarPasses[0]) / PERIOD + 100);
  const hookK = Math.min(1, Math.max(0, (t - T.hook) / 0.22));
  const cueK = Math.min(1, Math.max(0, (t - T.radarPasses[0] + 0.4) / 0.3));
  const tagK = Math.min(1, Math.max(0, (t - T.designated) / 0.18));
  const lit = (at: number) => Math.min(1, Math.max(0, (t - at) / 0.15));
  const contactAge = ageOf(BEARING, t);
  const contactLit = 0.28 + 0.72 * Math.exp(-contactAge / 0.5); // faint, but it is there on every sweep
  const edge = (a: number, r: number) => ({x: O.x + Math.cos((a * Math.PI) / 180) * r, y: O.y + Math.sin((a * Math.PI) / 180) * r});
  const a0 = BEARING - HALF - 4, a1 = BEARING + HALF + 4;

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height}>
        {/* range rings */}
        {[320, 640, 960].map((r, i) => {
          const p0 = edge(a0, r), p1 = edge(a1, r), lab = edge(a0 + 5, r);
          return (
            <g key={r}>
              <path d={`M ${p0.x} ${p0.y} A ${r} ${r} 0 0 1 ${p1.x} ${p1.y}`} fill="none" stroke="#1E3346" strokeWidth={1.5} />
              <text x={lab.x + 6} y={lab.y + 24} fill={colors.steel} opacity={0.75} fontFamily={fonts.mono} fontSize={30} letterSpacing={1.5}>{(i + 1) * 20} NM</text>
            </g>
          );
        })}
        {[a0, BEARING - HALF / 2, BEARING, BEARING + HALF / 2, a1].map((a) => {
          const p = edge(a, 1010);
          return <line key={a} x1={O.x} y1={O.y} x2={p.x} y2={p.y} stroke="#18293A" strokeWidth={1} />;
        })}
        {/* clutter painted by the sweep: different speckle every sweep */}
        {CLUTTER.map((c) => {
          const age = ageOf(c.bearing, t);
          if (age > 1.4) return null;
          const scan = scanNo(age);
          if (random(`ret${c.i}-${scan}`) > 0.42) return null;
          const lit = Math.exp(-age / 0.42);
          return <circle key={c.i} cx={c.x} cy={c.y} r={c.size} fill={colors.marlin} opacity={0.06 + 0.6 * lit * (0.5 + 0.5 * random(`amp${c.i}-${scan}`))} />;
        })}
        {/* the sweep, with afterglow behind it */}
        {Array.from({length: 14}, (_, i) => {
          const tt = t - i * 0.012;
          const a = (sweepAt(tt) * Math.PI) / 180;
          return <line key={i} x1={O.x} y1={O.y} x2={O.x + Math.cos(a) * 1010} y2={O.y + Math.sin(a) * 1010} stroke={colors.marlin}
            strokeOpacity={i === 0 ? 0.9 : 0.34 * (1 - i / 14)} strokeWidth={i === 0 ? 3 : 4} />;
        })}
        <line x1={O.x} y1={O.y} x2={O.x + Math.cos(sr) * 1010} y2={O.y + Math.sin(sr) * 1010} stroke={colors.marlin} strokeOpacity={0} />
        {/* cued search box */}
        <g transform={`rotate(${AOI.rot} ${AOI.cx} ${AOI.cy})`}>
          <rect x={AOI.cx - AOI.w / 2} y={AOI.cy - AOI.h / 2} width={AOI.w} height={AOI.h} fill="none" stroke={colors.white} strokeOpacity={0.75 * cueK} strokeWidth={2} strokeDasharray="12 9" />
          <text x={AOI.cx - AOI.w / 2 + 8} y={AOI.cy - AOI.h / 2 - 16} fill={colors.white} opacity={0.9 * cueK} fontFamily={fonts.mono} fontSize={36} letterSpacing={2}>INTEL CUE</text>
        </g>
        {/* the return that holds */}
        <circle cx={CONTACT.x} cy={CONTACT.y} r={6.5} fill={colors.white} opacity={contactLit} />
        <circle cx={CONTACT.x} cy={CONTACT.y} r={14} fill={colors.white} opacity={0.18 * Math.exp(-contactAge / 0.25)} />
        {t >= T.hook && (
          <g opacity={hookK} stroke={colors.threat} strokeWidth={3} fill="none">
            {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
              const d = 34 - hookK * 12;
              const x = CONTACT.x + sx * d, y = CONTACT.y + sy * d;
              return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 12} L ${x} ${y} L ${x - sx * 12} ${y}`} />;
            })}
            <g opacity={tagK}>
              <text x={CONTACT.x + 44} y={CONTACT.y - 6} fill={colors.threat} stroke={BG} strokeWidth={8} style={{paintOrder: 'stroke'}} fontFamily={fonts.mono} fontSize={40} letterSpacing={1}>TOI-01 · SUSPECT GO-FAST</text>
              <text x={CONTACT.x + 44} y={CONTACT.y + 40} fill={colors.threat} stroke={BG} strokeWidth={8} style={{paintOrder: 'stroke'}} fontFamily={fonts.mono} fontSize={34} letterSpacing={1}>NO NAV LTS · 30 KT</text>
            </g>
          </g>
        )}
        {/* own aircraft */}
        <g transform={`translate(${O.x} ${O.y - 20}) rotate(-90) scale(1.6)`}>
          <path d="M14 0 L-10 -3 L-12 -14 L-16 -14 L-14 -2 L-18 -1 L-18 1 L-14 2 L-16 14 L-12 14 L-10 3 Z" fill={colors.white} />
        </g>
      </svg>
      <div style={{position: 'absolute', top: 84, left: 40, fontFamily: fonts.mono, fontSize: 32, color: colors.steel, letterSpacing: '0.1em',
        border: `2px solid ${colors.steel}`, padding: '5px 14px', borderRadius: 4}}>MPA RADAR</div>
      {/* the enterprise's own status strip lights in order */}
      <div style={{position: 'absolute', top: 150, right: 64, display: 'flex', gap: 22, alignItems: 'center', fontFamily: fonts.mono, fontSize: 38, letterSpacing: '0.08em',
        border: `2px solid ${colors.white}`, padding: '10px 22px', borderRadius: 4, background: 'rgba(8,14,22,0.7)', opacity: lit(T.cue - 0.1)}}>
        {([['CUE', T.cue], ['DETECTED', T.detected], ['DESIGNATED', T.designated]] as [string, number][]).map(([w, at], i) => (
          <span key={w} style={{color: i === 2 ? colors.white : colors.marlin, opacity: 0.3 + 0.7 * lit(at), fontWeight: i === 2 ? 500 : 400}}>
            {w} {t >= at ? '✓' : ''}{i < 2 ? <span style={{color: colors.steel, marginLeft: 18}}>·</span> : null}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};
