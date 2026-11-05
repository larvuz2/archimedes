import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {colors, fonts} from '../theme';
import type {Super} from '../timeline';

const e = Easing.bezier(0.2, 0.8, 0.2, 1);

// One on-screen text element. `frame` is relative to the super's own start.
export const SuperEl: React.FC<{s: Super; dur: number}> = ({s, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const inP = e(Math.min(1, frame / (0.5 * fps)));
  const out = interpolate(frame, [dur - 8, dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o = inP * out;

  if (s.style === 'beat') {
    // Title: logo + product name, upper third
    return (
      <AbsoluteFill style={{alignItems: 'flex-start', paddingTop: 150, paddingLeft: 120, opacity: o}}>
        <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 340, marginLeft: 8, transform: `translateY(${(1 - inP) * 14}px)`}} />
        <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 150, letterSpacing: `${0.4 - inP * 0.14}em`,
          color: colors.white, marginTop: 18, textShadow: '0 4px 40px rgba(0,0,0,0.5)'}}>{s.text}</div>
      </AbsoluteFill>
    );
  }
  if (s.style === 'label') {
    const [num, ...rest] = s.text.split(' · ');
    return (
      <div style={{position: 'absolute', left: 110, bottom: 130, opacity: o, transform: `translateX(${(1 - inP) * -30}px)`,
        fontFamily: fonts.mono, color: colors.white, textShadow: '0 2px 18px rgba(0,0,0,0.6)'}}>
        <div style={{width: 60 * inP, height: 3, background: colors.marlin, marginBottom: 18}} />
        <span style={{color: colors.marlin, fontSize: 40, marginRight: 22}}>{rest.length ? num : ''}</span>
        <span style={{fontSize: 56, fontWeight: 500, letterSpacing: '0.12em'}}>{rest.length ? rest.join(' · ') : num}</span>
      </div>
    );
  }
  if (s.style === 'spec') {
    return (
      <div style={{position: 'absolute', left: 110, top: 110, opacity: o, border: `3px solid ${colors.white}`, borderRadius: 10,
        padding: '14px 30px', fontFamily: fonts.mono, fontSize: 64, color: colors.white, background: 'rgba(11,21,32,0.35)',
        backdropFilter: 'blur(6px)'}}>{s.text}</div>
    );
  }
  if (s.style === 'footnote') {
    return <div style={{position: 'absolute', right: 110, bottom: 70, opacity: o * 0.85, fontFamily: fonts.mono, fontSize: 24,
      color: colors.white}}>{s.text}</div>;
  }
  if (s.style === 'lock') {
    const size = 170 - inP * 30;
    const c = 26;
    const corner = (r: number) => ({position: 'absolute' as const, width: c, height: c, borderColor: colors.marlin, borderStyle: 'solid',
      borderWidth: 0, transform: `rotate(${r}deg)`, borderTopWidth: 4, borderLeftWidth: 4});
    return (
      <div style={{position: 'absolute', left: `${s.x}%`, top: `${s.y}%`, width: size * 1.6, height: size, transform: 'translate(-50%,-50%)', opacity: o}}>
        <div style={{...corner(0), left: 0, top: 0}} />
        <div style={{...corner(90), right: 0, top: 0}} />
        <div style={{...corner(180), right: 0, bottom: 0}} />
        <div style={{...corner(270), left: 0, bottom: 0}} />
        <div style={{position: 'absolute', right: 0, top: size + 16, whiteSpace: 'nowrap', textAlign: 'right', fontFamily: fonts.mono, fontSize: 26,
          color: frame < 0.9 * fps ? colors.threat : colors.marlin, letterSpacing: '0.08em', textShadow: '0 2px 12px rgba(0,0,0,0.7)'}}>
          {frame < 0.9 * fps ? 'SCANNING…' : s.text}
        </div>
      </div>
    );
  }
  if (s.style === 'recap') {
    // Three beats land on the VO words (offsets measured from the vo7 take)
    const words = s.text.split(' · ');
    const offsets = [0, 0.67, 2.01];
    return (
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-start', paddingTop: 150}}>
        <div style={{display: 'flex', gap: 60, fontFamily: fonts.display, fontWeight: 700, fontSize: 72, letterSpacing: '0.1em', color: colors.white,
          textShadow: '0 4px 30px rgba(0,0,0,0.6)'}}>
          {words.map((w, i) => {
            const f0 = offsets[i] * fps;
            const wo = e(Math.min(1, Math.max(0, (frame - f0) / 8))) * out;
            return <span key={w} style={{opacity: wo, transform: `scale(${1.15 - 0.15 * wo})`}}>{w}</span>;
          })}
        </div>
      </AbsoluteFill>
    );
  }
  return null;
};
