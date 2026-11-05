import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {fonts} from '../theme';
import {SHOTS, VERSION} from '../timeline';

// Review overlay: version chip, scene, timecode. Remove for final delivery.
export const AnimaticSlate: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const idx = Math.max(0, SHOTS.findIndex((s) => t >= s.start && t < s.end));
  const shot = SHOTS[idx];
  const tc = (() => {
    const s = Math.floor(t), ff = frame % fps;
    const p = (n: number) => String(n).padStart(2, '0');
    return `${p(Math.floor(s / 3600))}:${p(Math.floor(s / 60) % 60)}:${p(s % 60)}:${p(ff)}`;
  })();
  const chip: React.CSSProperties = {background: 'rgba(8,12,18,0.55)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.18)',
    borderRadius: 6, padding: '8px 14px', fontFamily: fonts.mono, fontSize: 18, color: 'rgba(255,255,255,0.88)', letterSpacing: '0.12em'};
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 28, right: 32, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8}}>
        <div style={{...chip, display: 'flex', alignItems: 'center', gap: 10, fontSize: 20, fontWeight: 500}}>
          <span style={{width: 10, height: 10, borderRadius: 5, background: '#F08A3C', display: 'inline-block'}} />
          {VERSION}
        </div>
        <div style={{...chip, fontSize: 15, padding: '6px 12px'}}>SC {String(idx + 1).padStart(2, '0')} · {shot.name.toUpperCase()}</div>
      </div>
      <div style={{position: 'absolute', top: 30, left: 32, ...chip, fontSize: 15, padding: '6px 12px', opacity: 0.85}}>
        ARCHIMEDES FREIGHT · MARLIN · CONCEPT VISUALIZATION · NOT FINAL
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 32, ...chip, fontSize: 18}}>TC {tc}</div>
    </AbsoluteFill>
  );
};
