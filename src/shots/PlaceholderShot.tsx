import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import type {Shot} from '../timeline';

// Animatic card used until each shot gets its real build.
export const PlaceholderShot: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const fade = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const progress = frame / durationInFrames;
  const tc = (shot.start + frame / fps).toFixed(1);

  return (
    <AbsoluteFill style={{background: colors.navy, color: colors.white, fontFamily: fonts.display, padding: 120, opacity: fade}}>
      <div style={{fontFamily: fonts.mono, color: colors.steel, fontSize: 28, letterSpacing: 4}}>
        ACT {shot.act} · SHOT {String(shot.id).padStart(2, '0')} · {shot.start}s–{shot.end}s · TC {tc}
      </div>
      <div style={{fontSize: 84, fontWeight: 700, marginTop: 24}}>{shot.name}</div>
      <div style={{fontSize: 44, fontStyle: 'italic', marginTop: 60, maxWidth: 1500, lineHeight: 1.35}}>“{shot.vo}”</div>
      <div style={{fontFamily: fonts.mono, fontSize: 28, color: colors.marlin, marginTop: 50}}>ON SCREEN: {shot.onScreen}</div>
      <div style={{fontFamily: fonts.mono, fontSize: 28, color: colors.threat, marginTop: 16}}>SOUND: {shot.sound}</div>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 8, width: `${progress * 100}%`, background: colors.threat}} />
    </AbsoluteFill>
  );
};
