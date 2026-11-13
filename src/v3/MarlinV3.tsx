import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, random, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import '../components/Fonts';
import {colors, fonts} from '../theme';
import {COP, type Camera} from './COP';
import {Radar} from './Radar';
import {Plate} from './Plate';
import {A0, toiAt} from './geo';
import {CONTACT_V3, DISCLAIMER_V3, SHOTS_V3, T, VERSION} from './timeline';
import tracks03 from '../../public/blender/shot03.tracks.json';
import tracks10 from '../../public/blender/shot10.tracks.json';
import tracks10ir from '../../public/blender/shot10_ir.tracks.json';

const e = Easing.bezier(0.2, 0.8, 0.2, 1);
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const smooth = (x: number) => x * x * (3 - 2 * x);

type Tracks = {tracks: Record<string, Record<string, number[]>>};
// screen position (px, 1920x1080) of a tracked 3D point on a given Blender frame
const track = (tr: Tracks, name: string, blenderFrame: number) => {
  const keys = Object.keys(tr.tracks).map(Number);
  const f = Math.min(Math.max(blenderFrame, Math.min(...keys)), Math.max(...keys));
  const p = tr.tracks[String(f)]?.[name];
  return p ? {x: p[0] * 1920, y: p[1] * 1080} : null;
};

// ---------- supers ----------
const Beat: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = e(Math.min(1, frame / (0.45 * fps)));
  const [num, ...rest] = text.split(' ');
  return (
    <div style={{position: 'absolute', left: 110, bottom: 130, opacity: k, transform: `translateX(${(1 - k) * -24}px)`, fontFamily: fonts.mono,
      color: colors.white, textShadow: '0 2px 18px rgba(0,0,0,0.8)'}}>
      <div style={{width: 56 * k, height: 3, background: colors.marlin, marginBottom: 16}} />
      <span style={{color: colors.marlin, fontSize: 34, marginRight: 18}}>{num}</span>
      <span style={{fontSize: 48, fontWeight: 500, letterSpacing: '0.2em'}}>{rest.join(' ')}</span>
    </div>
  );
};
const Footnote: React.FC<{text: string}> = ({text}) => (
  <div style={{position: 'absolute', right: 110, bottom: 96, fontFamily: fonts.mono, fontSize: 22, color: 'rgba(255,255,255,0.8)', textShadow: '0 1px 8px rgba(0,0,0,0.8)'}}>{text}</div>
);
const Words: React.FC<{start: number}> = ({start}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = start + frame / fps;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 175}}>
      <div style={{display: 'flex', gap: 46, fontFamily: fonts.mono, fontWeight: 500, fontSize: 54, letterSpacing: '0.3em', color: colors.white,
        textShadow: '0 2px 22px rgba(0,0,0,0.95)'}}>
        {['COVER.', 'SPRINT.', 'PERSIST.'].map((w, i) => {
          const k = e(ramp(t, T.vo.vo3 + T.vo3Words[i] - 0.04, T.vo.vo3 + T.vo3Words[i] + 0.22));
          return <span key={w} style={{opacity: k, transform: `scale(${1.12 - 0.12 * k})`}}>{w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- thermal sensor overlay ----------
const Brackets: React.FC<{cx: number; cy: number; w: number; h: number; k: number; color?: string}> = ({cx, cy, w, h, k, color = 'rgba(255,255,255,0.9)'}) => (
  <g stroke={color} strokeWidth={2.6} fill="none" opacity={k}>
    {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
      const x = cx + sx * (w / 2 + (1 - k) * 40), y = cy + sy * (h / 2 + (1 - k) * 26);
      return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 30} L ${x} ${y} L ${x - sx * 30} ${y}`} />;
    })}
  </g>
);

const IRFinish: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.6) 100%)'}} />
      <AbsoluteFill style={{opacity: 0.07, backgroundImage: 'repeating-linear-gradient(0deg, #fff 0 1px, transparent 1px 3px)'}} />
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('v3/grain.png')})`, backgroundSize: '512px 512px', opacity: 0.16, mixBlendMode: 'overlay',
        backgroundPosition: `${Math.floor(random(`ix${frame}`) * 512)}px ${Math.floor(random(`iy${frame}`) * 512)}px`}} />
    </>
  );
};

const irChip: React.CSSProperties = {fontFamily: fonts.mono, fontSize: 20, color: 'rgba(255,255,255,0.88)', letterSpacing: '0.14em'};

// 03 · Infrared ID: the aircraft's camera slews onto the contact; brackets and the tag land once it has it.
const Shot03: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = 7 + frame / fps;
  const p = track(tracks03 as Tracks, 'toi', frame + 1) ?? {x: 960, y: 540};
  const k = e(ramp(t, T.irSettle - 0.15, T.irSettle + 0.2));
  // readout runs while the turret slews, then holds on the storyboard's numbers
  const slew = 1 - e(ramp(t, 7.0, T.irSettle));
  const az = (214 + slew * 9.4).toFixed(0).padStart(3, '0');
  const el = (-38 - slew * 4.2).toFixed(0);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Plate src="blender/shot03.mp4" grain={0} vignette={0} style={{filter: 'grayscale(1) contrast(1.15) brightness(1.05)'}} />
      <IRFinish />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <g stroke="rgba(255,255,255,0.5)" strokeWidth={2}>
          <line x1={930} y1={540} x2={990} y2={540} /><line x1={960} y1={510} x2={960} y2={570} />
        </g>
        <Brackets cx={p.x} cy={p.y} w={900} h={380} k={k} />
      </svg>
      <div style={{...irChip, position: 'absolute', top: 92, left: 40}}>IR WHT</div>
      <div style={{...irChip, position: 'absolute', top: 124, right: 40}}>NFOV</div>
      <div style={{...irChip, position: 'absolute', bottom: 90, left: 40, fontSize: 18}}>AZ {az} EL {el}</div>
      <div style={{position: 'absolute', left: p.x - 250, top: p.y + 235, width: 500, textAlign: 'center', fontFamily: fonts.mono, fontSize: 24, color: colors.threat,
        letterSpacing: '0.12em', opacity: k, lineHeight: 1.5, textShadow: '0 0 10px rgba(0,0,0,1), 0 0 4px rgba(0,0,0,1)'}}>
        <div>TOI-01 · GO-FAST</div>
        <div>NO NAV LTS · 3 POB</div>
      </div>
    </AbsoluteFill>
  );
};

// 10 · Eyes on: Marlin's own infrared view (same look as shot 03), then pull out to the standoff.
const Shot10: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = 40 + frame / fps;
  const pull = smooth(ramp(t, T.irFull[1], T.irFull[1] + 0.55)); // the thermal view shrinks into the inset
  const W = 1920 - pull * (1920 - 520), H = (W * 9) / 16;
  const X = pull * (1920 - 520 - 64), Y = pull * 150;
  const ir = track(tracks10ir as Tracks, 'toi', frame + 1) ?? {x: 960, y: 540};
  const BF = frame + 1; // Blender frame of the beauty plate
  const mast = track(tracks10 as Tracks, 'mast', BF);
  const toi = track(tracks10 as Tracks, 'toi', BF);
  const los = e(ramp(t, 43.6, 44.3)); // line of sight appears once the Marlin has settled
  const plateStart = Math.round((33 / 24) * fps); // plate begins at Blender frame 34
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Sequence from={plateStart}><Plate src="blender/shot10.mp4" /></Sequence>
      {mast && toi && los > 0 && (
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
          <line x1={mast.x} y1={mast.y} x2={mast.x + (toi.x - mast.x) * los} y2={mast.y + (toi.y - mast.y) * los} stroke={colors.marlin} strokeOpacity={0.9}
            strokeWidth={2.2} strokeDasharray="9 8" />
          <circle cx={mast.x} cy={mast.y} r={7} fill="none" stroke={colors.marlin} strokeWidth={2} opacity={los} />
        </svg>
      )}
      {/* thermal view: full frame, then the live inset (top right, as on the storyboard) */}
      <div style={{position: 'absolute', left: X, top: Y, width: W, height: H, overflow: 'hidden', borderRadius: pull * 6,
        border: pull > 0.05 ? '2px solid rgba(255,255,255,0.75)' : 'none', boxShadow: pull > 0.05 ? '0 10px 40px rgba(0,0,0,0.6)' : 'none'}}>
        <div style={{width: 1920, height: 1080, transform: `scale(${W / 1920})`, transformOrigin: '0 0', position: 'relative'}}>
          <Plate src="blender/shot10_ir.mp4" grain={0} vignette={0} style={{filter: 'grayscale(1) contrast(1.15) brightness(1.05)'}} />
          <IRFinish />
          <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
            <Brackets cx={ir.x} cy={ir.y} w={1180} h={420} k={e(ramp(t, 40.15, 40.5))} />
          </svg>
          {pull < 0.3 && (
            <>
              <div style={{...irChip, position: 'absolute', top: 92, left: 40, opacity: 1 - pull * 3}}>IR WHT</div>
              <div style={{...irChip, position: 'absolute', top: 124, right: 40, opacity: 1 - pull * 3}}>NFOV</div>
            </>
          )}
          {pull > 0.5 && (
            <>
              <div style={{...irChip, position: 'absolute', top: 44, left: 52, fontSize: 62, opacity: ramp(pull, 0.6, 1)}}>02 EYES ON</div>
              <div style={{...irChip, position: 'absolute', bottom: 44, left: 52, fontSize: 62, display: 'flex', alignItems: 'center', gap: 26, opacity: ramp(pull, 0.6, 1)}}>
                <span style={{width: 34, height: 34, borderRadius: 17, background: colors.marlin, opacity: 0.45 + 0.55 * Math.round((Math.sin(t * 6) + 1) / 2)}} />LIVE
              </div>
            </>
          )}
        </div>
      </div>
      {t < T.surveil && <Sequence from={0} durationInFrames={Math.round((T.surveil - 40) * fps)}><Beat text="02 EYES ON" /></Sequence>}
      {t >= T.surveil && <Sequence from={Math.round((T.surveil - 40) * fps)}><Beat text="03 SURVEIL" /></Sequence>}
      {t > 42.9 && (
        <div style={{fontFamily: fonts.mono, fontSize: 19, letterSpacing: '0.14em', color: colors.white, position: 'absolute', top: 150, left: 110,
          border: `1.5px solid ${colors.white}`, padding: '7px 15px', borderRadius: 3, background: 'rgba(8,14,22,0.5)', opacity: ramp(t, 42.9, 43.3)}}>PARTNER EN ROUTE</div>
      )}
    </AbsoluteFill>
  );
};

// ---------- 12 · end card ----------
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = 56 + frame / fps;
  const land = (a: number) => interpolate(t, [a, a + 0.3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const toBlack = ramp(t, 59.6, 59.96);
  return (
    <AbsoluteFill style={{background: colors.navy, alignItems: 'center', justifyContent: 'center', color: colors.white}}>
      <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 400, opacity: land(T.logoLands)}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 140, letterSpacing: '0.3em', paddingLeft: '0.3em', marginTop: 34, opacity: land(T.logoLands)}}>MARLIN</div>
      <div style={{fontFamily: fonts.mono, fontSize: 36, letterSpacing: '0.12em', marginTop: 8, opacity: land(T.vo.vo4 + 0.4)}}>Cover. Sprint. Persist.</div>
      <div style={{width: 140, height: 4, background: colors.threat, margin: '38px 0', opacity: land(T.vo.vo4 + 0.6)}} />
      <div style={{fontFamily: fonts.mono, fontSize: 26, color: colors.steel, letterSpacing: '0.12em', opacity: land(T.vo.vo4 + 0.6)}}>{CONTACT_V3}</div>
      <div style={{position: 'absolute', bottom: 56, fontFamily: fonts.mono, fontSize: 17, color: colors.steel, maxWidth: 1500, textAlign: 'center', opacity: land(T.logoLands) * 0.9}}>{DISCLAIMER_V3}</div>
      <AbsoluteFill style={{background: '#000', opacity: toBlack}} />
    </AbsoluteFill>
  );
};

// ---------- review slate ----------
const Slate: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const shot = SHOTS_V3.find((s) => t >= s.start && t < s.end) ?? SHOTS_V3[SHOTS_V3.length - 1];
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
        <div style={{...chip, fontSize: 15, padding: '6px 12px'}}>SHOT {shot.n} · {shot.name.toUpperCase()}{shot.kind === '3D' ? ' · 3D PREVIZ' : ''}</div>
      </div>
      <div style={{position: 'absolute', top: 30, left: 32, ...chip, fontSize: 15, padding: '6px 12px', opacity: 0.85}}>
        ARCHIMEDES FREIGHT · MARLIN · STORYBOARD V5 · CONCEPT VISUALIZATION · NOT FINAL
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 32, ...chip, fontSize: 18}}>TC {tc}</div>
    </AbsoluteFill>
  );
};

// ---------- display cameras ----------
// 04: pull back from the contact to the common operational picture
const cam04 = (t: number): Camera => {
  const k = 1 - smooth(ramp(t, 10.0, 11.7));
  const c = toiAt(10);
  return {cx: 960 + (c.x - 960) * k, cy: 540 + (c.y - 540) * k, k: 1 + 1.5 * k};
};
// 08: back on the display, tight on the two closing tracks
const cam08 = (t: number): Camera => {
  const c = {x: (toiAt(31).x + A0.x) / 2 + 45, y: (toiAt(31).y + A0.y) / 2};
  return {cx: c.x, cy: c.y, k: 2.05 + ramp(t, 28, 34) * 0.18};
};
// 11: pull back to the full display, ending framed exactly like shot 04
const cam11 = (t: number): Camera => {
  const k = 1 - smooth(ramp(t, 46.0, 47.5));
  const c = toiAt(46);
  return {cx: 960 + (c.x - 40 - 960) * k, cy: 540 + (c.y + 30 - 540) * k, k: 1 + 0.9 * k};
};

export const MarlinV3: React.FC<{slate?: boolean}> = ({slate = true}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const seq = (a: number, b: number, el: React.ReactNode, name: string) => (
    <Sequence from={f(a)} durationInFrames={f(b) - f(a)} name={name}>{el}</Sequence>
  );
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {seq(0, 4, <Plate src="blender/shot01.mp4" />, '01 The boat')}
      {seq(4, 7, <Radar start={4} />, '02 Aircraft radar')}
      {seq(7, 10, <Shot03 />, '03 Infrared ID')}
      {seq(10, 20, <COP start={10} camera={cam04} />, '04-05 Out of reach / On station (same display, no cut)')}
      {seq(20, 23, <Plate src="blender/shot06.mp4" />, '06 Loiter')}
      {seq(23, 28, <Plate src="blender/shot07.mp4" />, '07 Lift')}
      {seq(23, 28, <Beat text="01 CLOSE" />, 'super 01 CLOSE')}
      {seq(T.vo.vo1, 34, <Footnote text="*Design target" />, 'footnote')}
      {seq(28, 34, <COP start={28} camera={cam08} showReadout />, '08 Converge')}
      {seq(34, 40, <Plate src="blender/shot09.mp4" />, '09 The run')}
      {seq(40, 46, <Shot10 />, '10 Eyes on')}
      {seq(46, 56, <COP start={46} camera={cam11} />, '11 The fleet')}
      {seq(46, 56, <Words start={46} />, 'COVER. SPRINT. PERSIST.')}
      {seq(56, 60, <EndCard />, '12 End card')}
      {/* sound: synthesized effects + score + narrator, mixed and mastered by scripts/build_audio_v3.py */}
      <Audio src={staticFile('audio/v3/mix.flac')} />
      {slate && <Slate />}
    </AbsoluteFill>
  );
};
