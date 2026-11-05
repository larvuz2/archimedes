import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import './components/Fonts';
import {SHOTS, VO_AT} from './timeline';
import {FrameShot} from './components/FrameShot';
import {SuperEl} from './components/Supers';
import {EndCard} from './components/EndCard';
import {AnimaticSlate} from './components/AnimaticSlate';
import {musicGain} from './audio';

// Hard cuts where the edit wants them (silence break into Marlin, music lift on the title).
const HARD_CUT = new Set(['f05', 'f06', 'f07']);

export const Marlin: React.FC<{slate?: boolean}> = ({slate = true}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SHOTS.map((s) => (
        <Sequence key={s.id} from={f(s.start)} durationInFrames={f(s.end) - f(s.start)} name={`${s.id} · ${s.name}`}>
          {s.image ? <FrameShot src={s.image} move={s.move} fadeIn={HARD_CUT.has(s.id) ? 0 : 6} /> : <EndCard />}
        </Sequence>
      ))}

      {SHOTS.flatMap((s) => (s.supers ?? []).map((sp, i) => {
        const dur = f(sp.until ?? s.end) - f(sp.at);
        return (
          <Sequence key={`${s.id}-sup-${i}`} from={f(sp.at)} durationInFrames={dur} name={`super · ${sp.text}`}>
            <SuperEl s={sp} dur={dur} />
          </Sequence>
        );
      }))}

      {/* Score: ElevenLabs Music via fal, level automation in src/audio.ts */}
      <Audio src={staticFile('audio/music/score.mp3')} volume={(fr) => musicGain(fr / fps)} />

      {/* Narrator: ElevenLabs v3 "Brian" via fal (scripts/generate_vo.py) */}
      {Object.entries(VO_AT).map(([id, at]) => (
        <Sequence key={id} from={f(at)} name={`VO ${id}`} layout="none">
          <Audio src={staticFile(`audio/vo/${id}.mp3`)} />
        </Sequence>
      ))}

      {slate && <AnimaticSlate />}
    </AbsoluteFill>
  );
};
