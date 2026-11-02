import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import './components/Fonts';
import {SHOTS} from './timeline';
import {PlaceholderShot} from './shots/PlaceholderShot';

// Master edit. Swap PlaceholderShot for each real shot component as it's built.
export const Marlin: React.FC = () => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SHOTS.map((s) => (
        <Sequence key={s.id} from={f(s.start)} durationInFrames={f(s.end - s.start)} name={`${s.id} · ${s.name}`}>
          <PlaceholderShot shot={s} />
        </Sequence>
      ))}

      {/* Narrator (scratch VO, fal.ai / ElevenLabs "Brian"). Regenerate with scripts/generate_vo.py */}
      {SHOTS.map((s) => (
        <Sequence key={`vo-${s.id}`} from={f(s.voAt)} name={`VO ${s.id}`} layout="none">
          <Audio src={staticFile(`audio/vo/shot-${String(s.id).padStart(2, '0')}.mp3`)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
