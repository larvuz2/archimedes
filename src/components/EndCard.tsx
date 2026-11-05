import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import {CONTACT, DISCLAIMER, VO_AT, SHOTS} from '../timeline';

export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const start = SHOTS.find((s) => s.id === 'end')!.start;
  const at = (s: number) => (s - start) * fps; // absolute seconds -> local frame
  const fade = (s: number) => interpolate(frame, [at(s), at(s) + 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const vo8 = VO_AT.vo8;
  return (
    <AbsoluteFill style={{background: colors.navy, alignItems: 'center', justifyContent: 'center', color: colors.white,
      opacity: interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'})}}>
      <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 420, opacity: fade(start)}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 130, letterSpacing: '0.3em', paddingLeft: '0.3em', marginTop: 30, opacity: fade(vo8)}}>MARLIN</div>
      <div style={{fontFamily: fonts.display, fontSize: 48, marginTop: 6, opacity: fade(vo8 + 0.8)}}>Speed is security.</div>
      <div style={{width: 140, height: 4, background: colors.threat, margin: '40px 0', opacity: fade(vo8 + 1.1)}} />
      <div style={{fontFamily: fonts.display, fontWeight: 600, fontSize: 34, opacity: fade(vo8 + 1.1)}}>{CONTACT.name}</div>
      <div style={{fontFamily: fonts.mono, fontSize: 28, color: colors.steel, marginTop: 8, opacity: fade(vo8 + 1.1)}}>{CONTACT.email}</div>
      <div style={{position: 'absolute', bottom: 60, fontFamily: fonts.mono, fontSize: 18, color: colors.steel, maxWidth: 1400,
        textAlign: 'center', opacity: fade(start + 0.3) * 0.9}}>{DISCLAIMER}</div>
    </AbsoluteFill>
  );
};
