import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts} from '../theme';
import type {Shot} from '../timeline';

// Storyboard animatic: the shot's sketch with a slow push, plus VO and notes.
// Used until each shot gets its real build.
export const PlaceholderShot: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const fade = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const push = interpolate(frame, [0, durationInFrames], [1, 1.06]);
  const progress = frame / durationInFrames;
  const tc = (shot.start + frame / fps).toFixed(1);

  return (
    <AbsoluteFill style={{background: colors.navy, color: colors.white, fontFamily: fonts.display, opacity: fade}}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-start', paddingTop: 70}}>
        <Img src={staticFile(shot.sketch)} style={{height: 720, transform: `scale(${push})`, borderRadius: 12}} />
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 24, left: 40, fontFamily: fonts.mono, color: colors.steel, fontSize: 24, letterSpacing: 3}}>
        ACT {shot.act} · SHOT {String(shot.id).padStart(2, '0')} · {shot.name.toUpperCase()} · {shot.start}s–{shot.end}s · TC {tc}
      </div>
      <div style={{position: 'absolute', left: 80, right: 80, bottom: 40}}>
        <div style={{fontSize: 38, fontStyle: 'italic', lineHeight: 1.3}}>“{shot.vo}”</div>
        <div style={{fontFamily: fonts.mono, fontSize: 22, color: colors.marlin, marginTop: 14}}>ON SCREEN: {shot.onScreen}</div>
        <div style={{fontFamily: fonts.mono, fontSize: 22, color: colors.threat, marginTop: 6}}>SOUND: {shot.sound}</div>
      </div>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 6, width: `${progress * 100}%`, background: colors.threat}} />
    </AbsoluteFill>
  );
};
