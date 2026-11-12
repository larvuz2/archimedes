import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import '../components/Fonts';
import {colors, fonts} from '../theme';
import {FrameShot} from '../components/FrameShot';
import {COP} from './COP';
import {Radar} from './Radar';
import {IRView} from './IRView';
import {A0, toiAt} from './geo';
import {CONTACT_V2, DISCLAIMER_V2, SHOTS_V2, VERSION, VO3_WORDS, VO_V2, VO_V2_LEN} from './timeline';

const e = Easing.bezier(0.2, 0.8, 0.2, 1);
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const smooth = (x: number) => x * x * (3 - 2 * x);

// ---------- supers ----------
const Beat: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = e(Math.min(1, frame / (0.5 * fps)));
  const [num, ...rest] = text.split(' ');
  return (
    <div style={{position: 'absolute', left: 110, bottom: 130, opacity: k, transform: `translateX(${(1 - k) * -24}px)`, fontFamily: fonts.mono,
      color: colors.white, textShadow: '0 2px 18px rgba(0,0,0,0.7)'}}>
      <div style={{width: 56 * k, height: 3, background: colors.marlin, marginBottom: 16}} />
      <span style={{color: colors.marlin, fontSize: 34, marginRight: 18}}>{num}</span>
      <span style={{fontSize: 48, fontWeight: 500, letterSpacing: '0.2em'}}>{rest.join(' ')}</span>
    </div>
  );
};
const Footnote: React.FC<{text: string}> = ({text}) => (
  <div style={{position: 'absolute', right: 110, bottom: 96, fontFamily: fonts.mono, fontSize: 22, color: 'rgba(255,255,255,0.8)'}}>{text}</div>
);
const Words: React.FC<{start: number}> = ({start}) => {
  // "COVER. SPRINT. PERSIST." one word per beat, on the VO words
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = start + frame / fps;
  const words = ['COVER.', 'SPRINT.', 'PERSIST.'];
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 175}}>
      <div style={{display: 'flex', gap: 46, fontFamily: fonts.mono, fontWeight: 500, fontSize: 54, letterSpacing: '0.3em', color: colors.white,
        textShadow: '0 2px 22px rgba(0,0,0,0.9)'}}>
        {words.map((w, i) => {
          const k = e(ramp(t, VO_V2.vo3 + VO3_WORDS[i] - 0.05, VO_V2.vo3 + VO3_WORDS[i] + 0.25));
          return <span key={w} style={{opacity: k, transform: `scale(${1.12 - 0.12 * k})`}}>{w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- shot 10: eyes on (IR full, then pull out to standoff with LIVE inset) ----------
const EyesOn: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = 40 + frame / fps;
  const pull = smooth(ramp(t, 41.5, 42.3)); // IR shrinks into the inset
  const insetW = 1920 - pull * (1920 - 560), insetH = insetW * 9 / 16;
  const insetX = pull * (1920 - 560 - 60), insetY = pull * (1080 - 315 - 150);
  const chip: React.CSSProperties = {fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.14em', color: colors.white};
  return (
    <AbsoluteFill>
      <Sequence from={0}><FrameShot src="frames/v2/a10b.jpg" move="pushIn" fadeIn={0} /></Sequence>
      <div style={{position: 'absolute', left: insetX, top: insetY, width: insetW, height: insetH, overflow: 'hidden',
        border: pull > 0.05 ? `2px solid rgba(255,255,255,0.7)` : 'none', borderRadius: pull * 6, boxShadow: pull > 0.05 ? '0 10px 40px rgba(0,0,0,0.6)' : 'none'}}>
        <div style={{width: 1920, height: 1080, transform: `scale(${insetW / 1920})`, transformOrigin: '0 0'}}>
          <IRView src="frames/v2/a10a.jpg" target={{x: 69, y: 52}} tag={pull < 0.2 ? ['TOI-01 · GO-FAST'] : undefined} tagPos={{left: 1180, top: 300}} slew={false}
            super={pull < 0.2 ? '02 EYES ON' : undefined} />
        </div>
        {pull > 0.5 && (
          <>
            <div style={{...chip, position: 'absolute', top: 12, left: 14, opacity: ramp(t, 42.1, 42.4)}}>02 EYES ON</div>
            <div style={{...chip, position: 'absolute', bottom: 12, left: 14, display: 'flex', alignItems: 'center', gap: 8, opacity: ramp(t, 42.1, 42.4)}}>
              <span style={{width: 10, height: 10, borderRadius: 5, background: colors.marlin, opacity: 0.5 + 0.5 * Math.round((Math.sin(t * 6) + 1) / 2)}} />LIVE
            </div>
          </>
        )}
      </div>
      {t > 42.6 && (
        <div style={{...chip, position: 'absolute', top: 150, left: 110, border: `1.5px solid ${colors.white}`, padding: '6px 14px', borderRadius: 3,
          background: 'rgba(8,14,22,0.45)', opacity: ramp(t, 42.6, 43.0)}}>PARTNER EN ROUTE</div>
      )}
      {t > 42.0 && <Sequence from={Math.round(2.0 * fps)}><Beat text="03 SURVEIL" /></Sequence>}
    </AbsoluteFill>
  );
};

// ---------- end card ----------
const EndCardV2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = 56 + frame / fps;
  const fade = (a: number) => interpolate(t, [a, a + 0.4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: colors.navy, alignItems: 'center', justifyContent: 'center', color: colors.white}}>
      <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 400, opacity: fade(56.6)}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 140, letterSpacing: '0.3em', paddingLeft: '0.3em', marginTop: 34, opacity: fade(VO_V2.vo4)}}>MARLIN</div>
      <div style={{fontFamily: fonts.mono, fontSize: 36, letterSpacing: '0.12em', marginTop: 8, opacity: fade(VO_V2.vo4 + 0.5)}}>Cover. Sprint. Persist.</div>
      <div style={{width: 140, height: 4, background: colors.threat, margin: '38px 0', opacity: fade(VO_V2.vo4 + 0.8)}} />
      <div style={{fontFamily: fonts.mono, fontSize: 26, color: colors.steel, letterSpacing: '0.12em', opacity: fade(VO_V2.vo4 + 0.8)}}>{CONTACT_V2}</div>
      <div style={{position: 'absolute', bottom: 56, fontFamily: fonts.mono, fontSize: 17, color: colors.steel, maxWidth: 1500, textAlign: 'center', opacity: fade(56.6) * 0.9}}>{DISCLAIMER_V2}</div>
    </AbsoluteFill>
  );
};

// ---------- review slate ----------
const Slate: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const shot = SHOTS_V2.find((s) => t >= s.start && t < s.end) ?? SHOTS_V2[SHOTS_V2.length - 1];
  const p = (n: number) => String(n).padStart(2, '0');
  const tc = `00:00:${p(Math.floor(t))}:${p(frame % fps)}`;
  const chip: React.CSSProperties = {background: 'rgba(8,12,18,0.55)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.18)',
    borderRadius: 6, padding: '8px 14px', fontFamily: fonts.mono, fontSize: 18, color: 'rgba(255,255,255,0.88)', letterSpacing: '0.12em'};
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 28, right: 32, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8}}>
        <div style={{...chip, display: 'flex', alignItems: 'center', gap: 10, fontSize: 20, fontWeight: 500}}>
          <span style={{width: 10, height: 10, borderRadius: 5, background: colors.threat, display: 'inline-block'}} />{VERSION}
        </div>
        <div style={{...chip, fontSize: 15, padding: '6px 12px'}}>SHOT {shot.n} · {shot.name.toUpperCase()}</div>
      </div>
      <div style={{position: 'absolute', top: 30, left: 32, ...chip, fontSize: 15, padding: '6px 12px', opacity: 0.85}}>
        ARCHIMEDES FREIGHT · MARLIN · STORYBOARD V5 · CONCEPT VISUALIZATION · NOT FINAL
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 32, ...chip, fontSize: 18}}>TC {tc}</div>
    </AbsoluteFill>
  );
};

// ---------- audio ----------
const VO_DUCK = (t: number) => {
  let d = 1;
  for (const id of Object.keys(VO_V2)) {
    const s = VO_V2[id], en = s + VO_V2_LEN[id];
    d = Math.min(d, 1 - 0.45 * smooth(ramp(t, s - 0.25, s)) * (1 - smooth(ramp(t, en, en + 0.4))));
  }
  return d;
};
// Act 1: hard pulse (score-v2), cut to silence as the track goes dashed
const act1Gain = (t: number) => 0.85 * (1 - smooth(ramp(t, 14.6, 15.4)));
// Act 2-3 cue laid twice, 3 phrases (12 s) apart, so the kick lands on the lift (23.4) and the
// final chord lands before the hard cut to the end card (56.0)
const CUE_A_OFFSET = 6.9; // cue time = t - 6.9 -> kick (cue 16.5) at 23.4
const CUE_B_OFFSET = 18.9; // cue time = t - 18.9
const cueAGain = (t: number) => smooth(ramp(t, 20.0, 20.8)) * (t < 23.4 ? 0.5 : 0.9) * (1 - smooth(ramp(t, 39.1, 39.5))) * VO_DUCK(t);
const cueBGain = (t: number) => smooth(ramp(t, 39.1, 39.5)) * (t < 46 ? 0.7 : 0.95) * (1 - smooth(ramp(t, 55.5, 56.0))) * VO_DUCK(t);

type Sfx = {src: string; at: number; vol: number; from?: number; fadeOut?: [number, number]};
const SFX: Sfx[] = [
  {src: 's01_outboards', at: 0, vol: 0.7, fadeOut: [3.8, 4.1]},
  {src: 's02_radar', at: 4.0, vol: 0.6, fadeOut: [6.8, 7.0]},
  {src: 's03_servo', at: 7.0, vol: 0.7},
  {src: 's01_outboards', at: 7.0, vol: 0.25, from: 1.0, fadeOut: [9.6, 10.0]},
  {src: 's04_console', at: 10.0, vol: 0.55, fadeOut: [14.6, 15.4]},
  {src: 's11_heldtone', at: 15.9, vol: 0.55, fadeOut: [19.8, 20.6]},
  {src: 's05_ocean', at: 20.0, vol: 0.7, fadeOut: [23.4, 24.6]},
  {src: 's06_spool', at: 22.8, vol: 0.85, fadeOut: [27.6, 28.2]},
  ...[28.6, 30.1, 31.6, 33.1].map((at) => ({src: 's07_datatone', at, vol: 0.5})),
  {src: 's08_roar', at: 33.9, vol: 0.75, fadeOut: [40.0, 40.6]},
  {src: 's09_rumble', at: 40.2, vol: 0.6, fadeOut: [45.6, 46.2]},
  ...[47.3, 47.6, 47.9].map((at) => ({src: 's07_datatone', at, vol: 0.35})),
  ...VO3_WORDS.map((w) => ({src: 's12_hit', at: VO_V2.vo3 + w - 0.02, vol: 0.75})),
  {src: 's10_rev', at: 58.1, vol: 0.55},
];

export const MarlinV2: React.FC<{slate?: boolean}> = ({slate = true}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const seq = (a: number, b: number, el: React.ReactNode, name: string) => (
    <Sequence from={f(a)} durationInFrames={f(b) - f(a)} name={name}>{el}</Sequence>
  );
  // shot 04 opens slightly tight and pulls back to the full picture
  const cam04 = (t: number) => ({cx: 960 + (1 - smooth(ramp(t, 10, 11.6))) * (toiAt(10).x - 960) * 0.5, cy: 540 + (1 - smooth(ramp(t, 10, 11.6))) * (toiAt(10).y - 540) * 0.5, k: 1 + (1 - smooth(ramp(t, 10, 11.6))) * 0.5});
  const cam08 = (t: number) => {
    const c = {x: (toiAt(31).x + A0.x) / 2 + 40, y: (toiAt(31).y + A0.y) / 2};
    return {cx: c.x, cy: c.y, k: 2.1 + ramp(t, 28, 34) * 0.15};
  };
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {seq(0, 4, <FrameShot src="frames/v2/a01.jpg" move="shake" fadeIn={0} />, '01 The boat')}
      {seq(4, 7, <Radar start={4} />, '02 Aircraft radar')}
      {seq(7, 10, <IRView src="frames/v2/a03.jpg" target={{x: 45, y: 47}} tag={['TOI-01 · GO-FAST', 'NO NAV LTS · 3 POB']} tagPos={{left: 250, top: 700}} readout="AZ 214 EL -38" />, '03 Infrared ID')}
      {seq(10, 20, <COP start={10} camera={cam04} />, '04-05 Out of reach / On station')}
      {seq(20, 23, <FrameShot src="frames/v2/a06.jpg" move="pushIn" fadeIn={0} />, '06 Loiter')}
      {seq(23, 28, <FrameShot src="frames/v2/a07.jpg" move="panLeft" fadeIn={0} />, '07 Lift')}
      {seq(23.4, 28, <Beat text="01 CLOSE" />, 'super 01 CLOSE')}
      {seq(23.4, 34, <Footnote text="*Design target" />, 'footnote')}
      {seq(28, 34, <COP start={28} camera={cam08} showReadout />, '08 Converge')}
      {seq(34, 40, <FrameShot src="frames/v2/a09.jpg" move="panRight" fadeIn={0} />, '09 The run')}
      {seq(40, 46, <EyesOn />, '10 Eyes on')}
      {seq(46, 56, <COP start={46} />, '11 The fleet')}
      {seq(46, 56, <Words start={46} />, 'COVER. SPRINT. PERSIST.')}
      {seq(56, 60, <EndCardV2 />, '12 End card')}

      {/* score */}
      <Audio src={staticFile('audio/music/score-v2.mp3')} startFrom={f(0.4)} volume={(fr) => act1Gain(fr / fps)} />
      <Sequence from={f(20.0)} name="score act 2 (A)">
        <Audio src={staticFile('audio/music/score-v2-act2.mp3')} startFrom={f(20.0 - CUE_A_OFFSET)} volume={(fr) => cueAGain(20.0 + fr / fps)} />
      </Sequence>
      <Sequence from={f(39.1)} name="score act 2 (B)">
        <Audio src={staticFile('audio/music/score-v2-act2.mp3')} startFrom={f(39.1 - CUE_B_OFFSET)} volume={(fr) => cueBGain(39.1 + fr / fps)} />
      </Sequence>

      {/* sound effects */}
      {SFX.map((x, i) => (
        <Sequence key={`sfx${i}`} from={f(x.at)} name={`sfx ${x.src}`}>
          <Audio src={staticFile(`audio/sfx/${x.src}.mp3`)} startFrom={x.from ? f(x.from) : undefined}
            volume={(fr) => {
              const t = x.at + fr / fps;
              return x.vol * (x.fadeOut ? 1 - smooth(ramp(t, x.fadeOut[0], x.fadeOut[1])) : 1) * (t < 56 || x.at >= 56 ? 1 : 0);
            }} />
        </Sequence>
      ))}

      {/* narrator: 20 words */}
      {Object.entries(VO_V2).map(([id, at]) => (
        <Sequence key={id} from={f(at)} name={`VO ${id}`} layout="none"><Audio src={staticFile(`audio/vo/${id}.mp3`)} /></Sequence>
      ))}

      {slate && <Slate />}
    </AbsoluteFill>
  );
};
