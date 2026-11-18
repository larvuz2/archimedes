import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import '../components/Fonts';
import {colors, fonts} from '../theme';
import {COP5, cam03, cam04, cam06, cam08, cam13} from './COP5';
import {Radar5} from './Radar5';
import {CONTACT_V5, DISCLAIMER_V5, HITS, SHOTS, T, VERSION, VO, fk, tk} from './timeline';
import tracks10 from '../../public/blender/shot10.tracks.json';
import tracks10ir from '../../public/blender/shot10_ir.tracks.json';
import tracksP1 from '../../public/blender/shotp1.tracks.json';
import tracksN1 from '../../public/blender/shotn1.tracks.json';
import tracksH1 from '../../public/blender/shoth1.tracks.json';

// Animatic v5.0: Storyboard V7, 14 shots, cut on the beat grid of the score (timeline.ts).
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const out3 = (x: number) => 1 - Math.pow(1 - x, 3);
const smooth = (x: number) => x * x * (3 - 2 * x);

type Tracks = {tracks: Record<string, Record<string, number[]>>};
const track = (tr: Tracks, name: string, blenderFrame: number) => {
  const keys = Object.keys(tr.tracks).map(Number);
  if (!keys.length) return null;
  const f = Math.min(Math.max(Math.round(blenderFrame), Math.min(...keys)), Math.max(...keys));
  const p = tr.tracks[String(f)]?.[name];
  return p ? {x: p[0] * 1920, y: p[1] * 1080} : null;
};

// ---------- plates ----------
const Grain: React.FC<{o?: number}> = ({o = 0.07}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundImage: `url(${staticFile('v3/grain.png')})`, backgroundSize: '512px 512px', opacity: o, mixBlendMode: 'overlay',
      backgroundPosition: `${Math.floor(random(`gx${frame}`) * 512)}px ${Math.floor(random(`gy${frame}`) * 512)}px`}} />
  );
};
const IRFinish: React.FC = () => (
  <>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.6) 100%)'}} />
    <AbsoluteFill style={{opacity: 0.07, backgroundImage: 'repeating-linear-gradient(0deg, #fff 0 1px, transparent 1px 3px)'}} />
    <Grain o={0.16} />
  </>
);
type ClipProps = {src: string; from?: number; rate?: number; z?: [number, number]; o?: [number, number]; ir?: boolean; dim?: number};
// A Blender plate, full frame, with a slow push so every cut keeps moving
const zoomAt = (frame: number, dur: number, z: [number, number]) => z[0] + (z[1] - z[0]) * (frame / Math.max(1, dur - 1));
const Clip: React.FC<ClipProps> = ({src, from = 0, rate = 1, z = [1.02, 1.07], o = [0.5, 0.5], ir, dim = 1}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const filter = `${ir ? 'grayscale(1) contrast(1.15) brightness(1.05) ' : ''}${dim !== 1 ? `brightness(${dim})` : ''}`.trim() || undefined;
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile(`blender/${src}.mp4`)} trimBefore={from} playbackRate={rate} muted
        style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoomAt(frame, durationInFrames, z)})`, transformOrigin: `${o[0] * 100}% ${o[1] * 100}%`, filter}} />
      {ir ? <IRFinish /> : (
        <>
          <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)'}} />
          <Grain />
        </>
      )}
    </AbsoluteFill>
  );
};
// map a tracked point through the same push-in as the plate
const onScreen = (p: {x: number; y: number} | null, zoom: number, o: [number, number]) => p && {x: o[0] * 1920 + (p.x - o[0] * 1920) * zoom, y: o[1] * 1080 + (p.y - o[1] * 1080) * zoom};

// ---------- overlays ----------
const mono = (size: number, color: string, extra: React.CSSProperties = {}): React.CSSProperties => ({fontFamily: fonts.mono, fontSize: size, letterSpacing: '0.14em', color, ...extra});
const boxed = (c: string, extra: React.CSSProperties = {}): React.CSSProperties => ({...mono(38, c, {letterSpacing: '0.1em'}), border: `2px solid ${c}`, padding: '9px 20px', borderRadius: 4, background: 'rgba(8,14,22,0.7)', ...extra});
const Brackets: React.FC<{cx: number; cy: number; w: number; h: number; k: number; color?: string}> = ({cx, cy, w, h, k, color = 'rgba(255,255,255,0.9)'}) => (
  <g stroke={color} strokeWidth={2.6} fill="none" opacity={k}>
    {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
      const x = cx + sx * (w / 2 + (1 - k) * 40), y = cy + sy * (h / 2 + (1 - k) * 26);
      return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 30} L ${x} ${y} L ${x - sx * 30} ${y}`} />;
    })}
  </g>
);
// section super: slams in on the downbeat, then settles to a small tag for the rest of the section
const Super: React.FC<{n: string; word: string; slam?: number}> = ({n, word, slam = 22}) => {
  const frame = useCurrentFrame();
  const k = out3(clamp(frame / 4));
  const big = 1 - smooth(ramp(frame, slam - 6, slam));
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 760px 300px at 330px 900px, rgba(4,8,13,0.62) 0%, rgba(4,8,13,0) 100%)'}} />
      <div style={{position: 'absolute', left: 110, bottom: 118, opacity: k, color: colors.white, textShadow: '0 4px 30px rgba(0,0,0,0.85)',
        transform: `scale(${(1.18 - 0.18 * k) * (0.55 + 0.45 * big)})`, transformOrigin: '0% 100%'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 20, ...mono(40, colors.marlin, {letterSpacing: '0.2em'})}}>
          <span style={{width: 90 * k, height: 5, background: colors.marlin}} />{n}
        </div>
        <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 170, letterSpacing: '0.12em', lineHeight: 1.05}}>{word}</div>
      </div>
    </AbsoluteFill>
  );
};
export const Readout: React.FC = () => {
  const frame = useCurrentFrame();
  const k = out3(clamp(frame / 5));
  return (
    <>
      <div style={{...boxed(colors.marlin), position: 'absolute', right: 110, bottom: 150, opacity: k, transform: `scale(${1.15 - 0.15 * k})`, transformOrigin: '100% 100%',
        fontSize: 62, fontWeight: 500, padding: '12px 28px', borderWidth: 2.5}}>50 NM · 30 MIN*</div>
      <div style={{position: 'absolute', right: 110, bottom: 100, ...mono(22, 'rgba(255,255,255,0.85)', {letterSpacing: '0.04em'}), opacity: k}}>*Design target</div>
    </>
  );
};

// 07 · Eyes on: Marlin's infrared view (three aboard, bales on deck, live to the watch floor), then pull out to the standoff
const EyesOn: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t0 = tk(45);
  const t = t0 + frame / fps;
  const pull = smooth(ramp(t, T.irPull, T.irPull + 0.55));
  const W = 1920 - pull * (1920 - 560), H = (W * 9) / 16;
  const X = pull * (1920 - 560 - 64), Y = pull * 150;
  const ir = track(tracks10ir as Tracks, 'toi', frame + 1) ?? {x: 960, y: 540};
  const BF = frame + 1;
  const mast = track(tracks10 as Tracks, 'mast', BF), toi = track(tracks10 as Tracks, 'toi', BF);
  const los = out3(ramp(t, T.irPull + 1.4, T.irPull + 2.0));
  const plateStart = Math.round((33 / 24) * fps);
  const irK = out3(ramp(t, t0 + 0.1, t0 + 0.4));
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Sequence from={plateStart}><Clip src="shot10" z={[1.0, 1.03]} /></Sequence>
      {mast && toi && los > 0 && (
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
          <line x1={mast.x} y1={mast.y} x2={mast.x + (toi.x - mast.x) * los} y2={mast.y + (toi.y - mast.y) * los} stroke={colors.marlin} strokeOpacity={0.9} strokeWidth={2.2} strokeDasharray="9 8" />
          <circle cx={mast.x} cy={mast.y} r={7} fill="none" stroke={colors.marlin} strokeWidth={2} opacity={los} />
        </svg>
      )}
      <div style={{position: 'absolute', left: X, top: Y, width: W, height: H, overflow: 'hidden', borderRadius: pull * 6,
        border: pull > 0.05 ? '2px solid rgba(255,255,255,0.75)' : 'none', boxShadow: pull > 0.05 ? '0 10px 40px rgba(0,0,0,0.6)' : 'none'}}>
        <div style={{width: 1920, height: 1080, transform: `scale(${W / 1920})`, transformOrigin: '0 0', position: 'relative'}}>
          <Clip src="shot10_ir" z={[1.0, 1.0]} ir />
          <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}><Brackets cx={ir.x} cy={ir.y} w={1180} h={420} k={irK} /></svg>
          <div style={{...mono(pull > 0.5 ? 104 : 40, 'rgba(255,255,255,0.92)', {letterSpacing: '0.08em'}), position: 'absolute', top: pull > 0.5 ? 40 : 84, left: pull > 0.5 ? 52 : 40}}>MARLIN IR</div>
          <div style={{...mono(pull > 0.5 ? 104 : 48, colors.threat, {letterSpacing: '0.08em'}), position: 'absolute', top: pull > 0.5 ? 40 : 150, right: pull > 0.5 ? 52 : 64, opacity: irK}}>3 POB · BALES</div>
          <div style={{...mono(pull > 0.5 ? 104 : 44, 'rgba(255,255,255,0.95)', {letterSpacing: '0.08em'}), position: 'absolute', bottom: pull > 0.5 ? 40 : 90, ...(pull > 0.5 ? {left: 52} : {right: 64}), display: 'flex', alignItems: 'center',
            gap: 22, opacity: irK}}>
            <span style={{width: pull > 0.5 ? 60 : 30, height: pull > 0.5 ? 60 : 30, borderRadius: 30, background: colors.marlin, opacity: 0.45 + 0.55 * Math.round((Math.sin(t * 6) + 1) / 2)}} />LIVE TO C2
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 09 · Pass (overhead). Callouts follow the plate's tracked points.
const Pass: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const FROM = 6, z: [number, number] = [1.0, 1.05], o: [number, number] = [0.5, 0.5];
  const zoom = zoomAt(frame, durationInFrames, z);
  const bf = FROM + frame + 1;
  const toi = onScreen(track(tracksP1 as Tracks, 'toi', bf), zoom, o), m = onScreen(track(tracksP1 as Tracks, 'marlin', bf), zoom, o);
  return (
    <AbsoluteFill>
      <Clip src="shotp1" from={FROM} z={z} o={o} />
      <div style={{...mono(34, colors.steel, {letterSpacing: '0.1em'}), position: 'absolute', top: 84, left: 40}}>NOTIONAL STOP PROFILE</div>
      <div style={{...mono(34, colors.steel, {letterSpacing: '0.1em'}), position: 'absolute', top: 150, right: 64}}>OVERHEAD</div>
      {toi && <div style={{...mono(40, colors.threat, {letterSpacing: '0.08em'}), position: 'absolute', left: toi.x - 85, top: toi.y + 44, textShadow: '0 0 10px #000, 0 0 4px #000'}}>TOI-01</div>}
      {m && <div style={{...mono(40, colors.marlin, {letterSpacing: '0.08em'}), position: 'absolute', left: m.x - 150, top: m.y - 96, textShadow: '0 0 10px #000, 0 0 4px #000'}}>LEAD MARLIN</div>}
    </AbsoluteFill>
  );
};

// 10 · Net away (overhead). Dashed turn arrows show that a swerve either way meets a leg.
const NetAway: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const FROM = 6, z: [number, number] = [1.0, 1.04], o: [number, number] = [0.5, 0.5];
  const zoom = zoomAt(frame, durationInFrames, z);
  const bf = FROM + frame + 1;
  const g = (n: string) => onScreen(track(tracksN1 as Tracks, n, bf), zoom, o);
  const bow = g('bow'), apex = g('apex'), eL = g('endL'), eR = g('endR'), toi = g('toi');
  const t = frame / fps; // shot time; the net fires at 0.65 s, the ends land at about 1.9 s
  const fired = out3(ramp(t, 0.62, 0.8));
  const arrows = smooth(ramp(t, 2.0, 2.6));
  const curve = (end: {x: number; y: number}) => {
    if (!bow || !apex) return null;
    const mid = {x: apex.x + (end.x - apex.x) * 0.45, y: apex.y + (end.y - apex.y) * 0.45};
    const c = {x: bow.x + (mid.x - bow.x) * 0.35, y: bow.y + (mid.y - bow.y) * 0.05};
    const pts = Array.from({length: 21}, (_, i) => {
      const u = (i / 20) * arrows, m1 = 1 - u;
      return {x: m1 * m1 * bow.x + 2 * m1 * u * c.x + u * u * mid.x, y: m1 * m1 * bow.y + 2 * m1 * u * c.y + u * u * mid.y};
    });
    const a = pts[pts.length - 2], b = pts[pts.length - 1];
    const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    return (
      <g>
        <polyline points={pts.map((p) => `${p.x},${p.y}`).join(' ')} fill="none" stroke={colors.threat} strokeWidth={2.6} strokeDasharray="8 7" />
        {arrows > 0.95 && <path d="M0 0 L-14 -7 L-14 7 Z" fill={colors.threat} transform={`translate(${b.x} ${b.y}) rotate(${ang})`} />}
      </g>
    );
  };
  return (
    <AbsoluteFill>
      <Clip src="shotn1" from={FROM} z={z} o={o} />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {arrows > 0 && eL && curve(eL)}
        {arrows > 0 && eR && curve(eR)}
      </svg>
      <div style={{...mono(34, colors.steel, {letterSpacing: '0.1em'}), position: 'absolute', top: 84, left: 40}}>NOTIONAL STOP PROFILE</div>
      <div style={{position: 'absolute', top: 150, right: 64, ...boxed(colors.white, {fontSize: 40})}}>C2 · STOP AUTHORIZED · PROFILE: V-NET</div>
      {toi && <div style={{...mono(40, colors.threat, {letterSpacing: '0.08em'}), position: 'absolute', left: toi.x - 170, top: toi.y + 44, textShadow: '0 0 10px #000, 0 0 4px #000'}}>TOI-01 · 30 KT</div>}
      <div style={{...boxed(colors.white, {fontSize: 64, fontWeight: 500, padding: '12px 30px', borderWidth: 3}), position: 'absolute', right: 110, bottom: 150, opacity: fired,
        transform: `scale(${1.2 - 0.2 * fired})`, transformOrigin: '100% 100%'}}>NET AWAY</div>
    </AbsoluteFill>
  );
};

// 11 · Fouled. Wide; quick underwater cutaway in an inset as the props ingest the net; the track tag changes to DIW.
const RATE11 = 0.87;
const Fouled: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = tk(72) + frame / fps;
  const insetIn = T.foul - 0.15, insetOut = T.foul + 1.75;
  const ik = out3(ramp(t, insetIn, insetIn + 0.18)) * (1 - ramp(t, insetOut - 0.15, insetOut));
  const diw = out3(ramp(t, T.diw, T.diw + 0.2));
  return (
    <AbsoluteFill>
      <Clip src="shotx1" rate={RATE11} z={[1.0, 1.06]} o={[0.55, 0.55]} />
      {ik > 0 && (
        <Sequence from={Math.round((insetIn - tk(72)) * fps)}>
          <div style={{position: 'absolute', left: 64, bottom: 110, width: 720, height: 405, overflow: 'hidden', borderRadius: 6, border: '2px solid rgba(255,255,255,0.8)',
            boxShadow: '0 10px 40px rgba(0,0,0,0.6)', opacity: ik, transform: `scale(${0.94 + 0.06 * ik})`, transformOrigin: '0% 100%'}}>
            <div style={{width: 1920, height: 1080, transform: `scale(${720 / 1920})`, transformOrigin: '0 0', position: 'relative'}}>
              <Clip src="shotu1" from={4} z={[1.05, 1.12]} />
              <div style={{...mono(104, colors.white, {letterSpacing: '0.08em'}), position: 'absolute', top: 40, left: 50, border: '5px solid #fff', padding: '10px 30px', borderRadius: 8, background: 'rgba(8,14,22,0.7)'}}>PROP FOULED</div>
            </div>
          </div>
        </Sequence>
      )}
      <div style={{position: 'absolute', top: 150, left: 110, ...boxed(colors.threat, {fontSize: 56, fontWeight: 500, borderWidth: 3}), opacity: diw,
        transform: `scale(${1.25 - 0.25 * diw})`, transformOrigin: '0% 0%'}}>TOI-01 · DIW</div>
    </AbsoluteFill>
  );
};

// 12 · Hold. Both Marlins hold at standoff with eyes on; the partner is closing.
const RATE12 = 0.87;
const Hold: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const z: [number, number] = [1.0, 1.05], o: [number, number] = [0.45, 0.55];
  const zoom = zoomAt(frame, durationInFrames, z);
  const bf = frame * RATE12 + 1;
  const mast = onScreen(track(tracksH1 as Tracks, 'mast', bf), zoom, o), toi = onScreen(track(tracksH1 as Tracks, 'toi', bf), zoom, o);
  const pt = onScreen(track(tracksH1 as Tracks, 'partner', bf), zoom, o);
  const t = frame / fps;
  const los = out3(ramp(t, 0.3, 0.9));
  return (
    <AbsoluteFill>
      <Clip src="shoth1" rate={RATE12} z={z} o={o} />
      {mast && toi && (
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
          <line x1={mast.x} y1={mast.y} x2={mast.x + (toi.x - mast.x) * los} y2={mast.y + (toi.y - mast.y) * los} stroke={colors.marlin} strokeOpacity={0.9} strokeWidth={2.4} strokeDasharray="9 8" />
          <circle cx={mast.x} cy={mast.y} r={7} fill="none" stroke={colors.marlin} strokeWidth={2} opacity={los} />
        </svg>
      )}
      {pt && <div style={{...mono(38, colors.white, {letterSpacing: '0.08em'}), position: 'absolute', left: pt.x - 90, top: pt.y - 84, textShadow: '0 0 10px #000, 0 0 4px #000', opacity: out3(ramp(t, 0.5, 0.9))}}>PARTNER</div>}
      <div style={{position: 'absolute', top: 150, left: 110, display: 'flex', gap: 14}}>
        <div style={boxed(colors.white, {opacity: out3(ramp(t, 0.15, 0.4))})}>PARTNER EN ROUTE</div>
        <div style={boxed(colors.threat)}>DIW</div>
      </div>
    </AbsoluteFill>
  );
};

// 13 · The three words land one per hit over the fleet map
const WORDS = ['INTERCEPT.', 'SURVEIL.', 'STOP.'];
const Words: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = tk(88) + frame / fps;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 150}}>
      <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(4,8,13,0.75) 0%, rgba(4,8,13,0) 38%)'}} />
      <div style={{display: 'flex', gap: 56, fontFamily: fonts.display, fontWeight: 700, fontSize: 96, letterSpacing: '0.12em', color: colors.white, textShadow: '0 4px 30px rgba(0,0,0,0.95)'}}>
        {WORDS.map((w, i) => {
          const k = out3(ramp(t, T.words[i] - 0.02, T.words[i] + 0.16));
          return <span key={w} style={{opacity: k, transform: `scale(${1.35 - 0.35 * k})`, display: 'inline-block'}}>{w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};

// 14 · End card: hard cut to navy, a beat of silence, then logo and name
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = tk(97) + frame / fps;
  const land = (a: number, d = 0.25) => out3(ramp(t, a, a + d));
  const tag = VO.l6 + 0.75;
  return (
    <AbsoluteFill style={{background: colors.navy, alignItems: 'center', justifyContent: 'center', color: colors.white}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 42%, rgba(79,209,197,0.09) 0%, rgba(0,0,0,0) 55%)', opacity: land(T.logo)}} />
      <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 400, opacity: land(T.logo)}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 150, letterSpacing: '0.3em', paddingLeft: '0.3em', marginTop: 34, opacity: land(T.logo, 0.12),
        transform: `scale(${1.1 - 0.1 * land(T.logo)})`}}>MARLIN</div>
      <div style={{...mono(56, colors.white, {letterSpacing: '0.12em'}), marginTop: 10, opacity: land(tag)}}>Intercept. Surveil. Stop.</div>
      <div style={{width: 140 * land(tag + 0.3), height: 4, background: colors.threat, margin: '38px 0'}} />
      <div style={{...mono(40, colors.steel, {letterSpacing: '0.1em'}), opacity: land(tag + 0.3)}}>{CONTACT_V5}</div>
      <div style={{position: 'absolute', bottom: 40, ...mono(24, colors.steel, {letterSpacing: '0.02em'}), maxWidth: 1480, textAlign: 'center', lineHeight: 1.35, opacity: 0.9 * land(T.logo + 0.2)}}>{DISCLAIMER_V5}</div>
      <AbsoluteFill style={{background: '#000', opacity: clamp((frame - (durationInFrames - 12)) / 11)}} />
    </AbsoluteFill>
  );
};

// ---------- review slate ----------
const Slate: React.FC<{version: string}> = ({version}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const shot = SHOTS.find((s) => frame >= fk(s.k0) && frame < fk(s.k1)) ?? SHOTS[SHOTS.length - 1];
  const p = (n: number) => String(n).padStart(2, '0');
  const tc = `00:00:${p(Math.floor(frame / fps))}:${p(frame % fps)}`;
  const chip: React.CSSProperties = {background: 'rgba(8,12,18,0.55)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: 6,
    padding: '8px 14px', ...mono(18, 'rgba(255,255,255,0.88)', {letterSpacing: '0.12em'})};
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 28, right: 32, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8}}>
        <div style={{...chip, display: 'flex', alignItems: 'center', gap: 10, fontSize: 20, fontWeight: 500}}>
          <span style={{width: 10, height: 10, borderRadius: 5, background: colors.threat, display: 'inline-block'}} />{version}
        </div>
        <div style={{...chip, fontSize: 15, padding: '6px 12px'}}>SHOT {shot.n} · {shot.name.toUpperCase()}</div>
      </div>
      <div style={{position: 'absolute', top: 30, left: 32, ...chip, fontSize: 15, padding: '6px 12px', opacity: 0.85}}>
        ARCHIMEDES FREIGHT · MARLIN · STORYBOARD V7 · CONCEPT VISUALIZATION · NOT FINAL
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 32, ...chip}}>TC {tc}</div>
    </AbsoluteFill>
  );
};

// ---------- the cut ----------
const at = (k: number) => tk(k);
type Cut = [k0: number, k1: number, el: React.ReactNode, name: string];
const CUTS: Cut[] = [
  // Act 1 · The gap. No narration: outboards, radar, a sinking score.
  [0, 4, <Clip src="shot01" from={0} z={[1.03, 1.1]} o={[0.5, 0.55]} />, '01 the boat: bow and spray'],
  [4, 7, <Clip src="shot01" from={50} z={[1.22, 1.32]} o={[0.2, 0.42]} />, '01 the boat: the crew'],
  [7, 16, <Radar5 start={at(7)} />, '02 detected and designated'],
  [16, 24, <COP5 start={at(16)} camera={cam03} />, '03 no end game'],
  // Act 2 · Intercept
  [24, 32, <COP5 start={at(24)} camera={cam04} />, '04 tasked'],
  [32, 33, <Clip src="shotf1" from={10} z={[1.0, 1.06]} />, '05 lift: the fan spools up'],
  [33, 38, <Clip src="shot07" from={14} z={[1.0, 1.05]} o={[0.45, 0.55]} />, '05 lift: onto the foils and gone'],
  [38, 45, <COP5 start={at(38)} camera={cam06} readout />, '06 converge'],
  [45, 54, <EyesOn />, '07 eyes on'],
  // Act 3 · The stop
  [54, 60, <COP5 start={at(54)} camera={cam08} stopProfile />, '08 authorized'],
  [60, 66, <Pass />, '09 pass'],
  [66, 72, <NetAway />, '10 net away'],
  [72, 80, <Fouled />, '11 fouled'],
  [80, 88, <Hold />, '12 hold'],
  // Act 4 · Coverage
  [88, 97, <COP5 start={at(88)} camera={cam13} />, '13 the fleet'],
  [97, 105, <EndCard />, '14 end card'],
];
const SUPERS: Cut[] = [
  [32, 45, <Super n="01" word="INTERCEPT" />, '01 INTERCEPT'],
  [45, 54, <Super n="02" word="SURVEIL" />, '02 SURVEIL'],
  [60, 72, <Super n="03" word="STOP" />, '03 STOP'],
  [88, 97, <Words />, 'INTERCEPT. SURVEIL. STOP.'],
];

const useHit = () => {
  const frame = useCurrentFrame();
  let flash = 0, dx = 0, dy = 0;
  HITS.forEach(([k, a]) => {
    const d = frame - fk(k);
    if (d >= 0 && d < 5) flash = Math.max(flash, a * 0.45 * (1 - d / 5));
    if (d >= 0 && d < 10) {
      const amp = a * 10 * Math.pow(1 - d / 10, 2);
      dx += amp * Math.sin(d * 2.4 + k);
      dy += amp * Math.cos(d * 3.1 + k * 1.7);
    }
  });
  return {flash, dx, dy};
};

// Two options of v5.1 share the picture and differ only in the narrator: A (Callum, v5.0's read) and B (a deeper, epic voice).
export const MarlinV5: React.FC<{slate?: boolean; audio?: string; version?: string}> = ({slate = true, audio = 'audio/v5/mix.flac', version = VERSION}) => {
  const {durationInFrames} = useVideoConfig();
  const {flash, dx, dy} = useHit();
  const seq = ([k0, k1, el, name]: Cut, i: number, pre = '') => (
    <Sequence key={`${pre}${i}`} from={fk(k0)} durationInFrames={Math.min(durationInFrames, fk(k1)) - fk(k0)} name={`${pre}${k0}-${k1} ${name}`}>{el}</Sequence>
  );
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{transform: `translate(${dx}px, ${dy}px) scale(1.012)`}}>
        {CUTS.map((c, i) => seq(c, i))}
        {SUPERS.map((s, i) => seq(s, i, 'super '))}
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
      {/* sound: score, designed effects and narrator on the same beat grid, mixed and mastered by scripts/build_audio_v5.py */}
      <Audio src={staticFile(audio)} />
      {slate && <Slate version={version} />}
    </AbsoluteFill>
  );
};
