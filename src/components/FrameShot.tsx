import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import type {Move} from '../timeline';

const ease = Easing.bezier(0.33, 0, 0.2, 1);

// Full-bleed storyboard frame with a slow camera move and a light film finish.
export const FrameShot: React.FC<{src: string; move: Move; fadeIn?: number}> = ({src, move, fadeIn = 6}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = ease(Math.min(1, frame / durationInFrames));
  const lerp = (a: number, b: number) => a + (b - a) * p;

  let scale = 1.06, x = 0, y = 0;
  switch (move) {
    case 'pushIn': scale = lerp(1.04, 1.14); break;
    case 'pullOut': scale = lerp(1.14, 1.04); break;
    case 'panRight': scale = 1.12; x = lerp(2.5, -2.5); break;
    case 'panLeft': scale = 1.12; x = lerp(-2.5, 2.5); break;
    case 'rise': scale = lerp(1.08, 1.13); y = lerp(2.5, -2); break;
    case 'still': scale = 1.04; break;
    case 'shake': // tight, moving with the boat
      scale = lerp(1.1, 1.16);
      x = Math.sin(frame * 0.9) * 0.35 + Math.sin(frame * 2.3) * 0.2;
      y = Math.cos(frame * 1.1) * 0.45 + Math.sin(frame * 3.1) * 0.15;
      break;
  }
  const opacity = fadeIn ? interpolate(frame, [0, fadeIn], [0, 1], {extrapolateRight: 'clamp'}) : 1;

  return (
    <AbsoluteFill style={{background: '#000', opacity, overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover',
        transform: `scale(${scale}) translate(${x}%, ${y}%)`}} />
      {/* vignette */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)'}} />
    </AbsoluteFill>
  );
};
