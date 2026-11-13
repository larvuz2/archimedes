import React from 'react';
import {AbsoluteFill, OffthreadVideo, random, staticFile, useCurrentFrame} from 'remotion';

// A Blender plate (rendered 1280x720, shown full frame) with a light film finish.
export const Plate: React.FC<{src: string; grain?: number; vignette?: number; style?: React.CSSProperties}> = ({src, grain = 0.07, vignette = 0.42, style}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover', ...style}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 58%, rgba(0,0,0,${vignette}) 100%)`}} />
      {grain > 0 && (
        <AbsoluteFill style={{backgroundImage: `url(${staticFile('v3/grain.png')})`, backgroundSize: '512px 512px', opacity: grain, mixBlendMode: 'overlay',
          backgroundPosition: `${Math.floor(random(`gx${frame}`) * 512)}px ${Math.floor(random(`gy${frame}`) * 512)}px`}} />
      )}
    </AbsoluteFill>
  );
};
