import React from 'react';
import {AbsoluteFill, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';

// Patrol aircraft sea-search radar (generic depiction: no model, band or range performance).
const O = {x: 960, y: 1050};
const BG = '#0B1520';
const clutter = Array.from({length: 520}, (_, i) => {
  const r = Math.pow(random(`r${i}`), 1.7) * 980 + 30;
  const a = (-150 + random(`a${i}`) * 120) * (Math.PI / 180);
  return {x: O.x + Math.cos(a) * r, y: O.y + Math.sin(a) * r, s: 1 + random(`s${i}`) * 2.2, seed: i};
});
const CONTACT = {x: 1090, y: 470};

export const Radar: React.FC<{start: number}> = ({start}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = start + frame / fps;
  const local = frame / fps;
  // sector scan: sweeps back and forth across +/-60 deg
  const sweep = -90 + Math.sin(local * 2.4) * 58;
  const sweepRad = (sweep * Math.PI) / 180;
  const angleOf = (p: {x: number; y: number}) => (Math.atan2(p.y - O.y, p.x - O.x) * 180) / Math.PI;
  const lit = (p: {x: number; y: number}) => Math.max(0, 1 - Math.abs(angleOf(p) - sweep) / 9);
  const contactLit = Math.max(lit(CONTACT), local > 0.6 ? 0.55 : 0); // holds sweep after sweep
  const hooked = t > 5.7;
  const hookK = Math.min(1, Math.max(0, (t - 5.7) / 0.25));

  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={width} height={height}>
        <defs>
          <radialGradient id="beam" cx="0" cy="0" r="1"><stop offset="0" stopColor={colors.marlin} stopOpacity="0.5" /><stop offset="1" stopColor={colors.marlin} stopOpacity="0" /></radialGradient>
        </defs>
        {[330, 660, 990].map((r, i) => (
          <g key={r}>
            <path d={`M ${O.x + Math.cos((-150 * Math.PI) / 180) * r} ${O.y + Math.sin((-150 * Math.PI) / 180) * r} A ${r} ${r} 0 0 1 ${O.x + Math.cos((-30 * Math.PI) / 180) * r} ${O.y + Math.sin((-30 * Math.PI) / 180) * r}`}
              fill="none" stroke="#1E3346" strokeWidth={1.5} />
            <text x={O.x + 8} y={O.y - r + 22} fill={colors.steel} opacity={0.7} fontFamily={fonts.mono} fontSize={16}>{(i + 1) * 20} NM</text>
          </g>
        ))}
        {[-150, -120, -90, -60, -30].map((a) => (
          <line key={a} x1={O.x} y1={O.y} x2={O.x + Math.cos((a * Math.PI) / 180) * 1000} y2={O.y + Math.sin((a * Math.PI) / 180) * 1000} stroke="#1A2D3F" strokeWidth={1} />
        ))}
        {clutter.map((c) => (
          <circle key={c.seed} cx={c.x} cy={c.y} r={c.s} fill={colors.marlin} opacity={0.08 + lit(c) * 0.6 * random(`f${c.seed}-${Math.floor(local * 6)}`)} />
        ))}
        {/* beam with afterglow */}
        {Array.from({length: 10}, (_, i) => {
          const a = sweepRad - Math.cos(local * 2.4) * i * 0.012;
          return <line key={i} x1={O.x} y1={O.y} x2={O.x + Math.cos(a) * 1000} y2={O.y + Math.sin(a) * 1000} stroke={colors.marlin} strokeOpacity={0.55 - i * 0.05} strokeWidth={i === 0 ? 3 : 2} />;
        })}
        {/* cued search box (AOI) */}
        <g transform={`rotate(-12 ${CONTACT.x} ${CONTACT.y})`}>
          <rect x={CONTACT.x - 260} y={CONTACT.y - 130} width={480} height={250} fill="none" stroke={colors.white} strokeOpacity={0.7} strokeWidth={2} strokeDasharray="12 9" />
          <text x={CONTACT.x - 250} y={CONTACT.y - 142} fill={colors.white} opacity={0.75} fontFamily={fonts.mono} fontSize={18} letterSpacing={2}>AOI</text>
        </g>
        {/* the return */}
        <circle cx={CONTACT.x} cy={CONTACT.y} r={7} fill={colors.white} opacity={0.35 + contactLit * 0.65} />
        {hooked && (
          <g opacity={hookK} stroke={colors.threat} strokeWidth={3} fill="none">
            {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
              const d = 30 - hookK * 8;
              const x = CONTACT.x + sx * d, y = CONTACT.y + sy * d;
              return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 12} L ${x} ${y} L ${x - sx * 12} ${y}`} />;
            })}
            <text x={CONTACT.x + 38} y={CONTACT.y + 6} fill={colors.threat} stroke="none" fontFamily={fonts.mono} fontSize={20} letterSpacing={2}>CONTACT</text>
          </g>
        )}
        {/* own aircraft */}
        <g transform={`translate(${O.x} ${O.y - 18}) rotate(-90) scale(1.6)`}>
          <path d="M14 0 L-10 -3 L-12 -14 L-16 -14 L-14 -2 L-18 -1 L-18 1 L-14 2 L-16 14 L-12 14 L-10 3 Z" fill={colors.white} />
        </g>
      </svg>
      <div style={{position: 'absolute', top: 92, left: 40, fontFamily: fonts.mono, fontSize: 18, color: colors.steel, letterSpacing: '0.12em', border: `1.5px solid ${colors.steel}`, padding: '4px 10px', borderRadius: 3}}>RADAR</div>
    </AbsoluteFill>
  );
};
