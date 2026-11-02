import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import './components/Fonts';
import {SHOTS} from './timeline';
import {PlaceholderShot} from './shots/PlaceholderShot';

// Master edit. Swap PlaceholderShot for each real shot component as it's built.
export const Marlin: React.FC = () => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SHOTS.map((s) => (
        <Sequence key={s.id} from={Math.round(s.start * fps)} durationInFrames={Math.round((s.end - s.start) * fps)} name={`${s.id} · ${s.name}`}>
          <PlaceholderShot shot={s} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
