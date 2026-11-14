import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import '../components/Fonts';
import {colors, fonts} from '../theme';
import {Map, contactAt, partnerAt, type Camera} from './Map';
import {CONTACT_V4, DISCLAIMER_V4, HITS, K, SECTIONS, VERSION, VO, fk, tk} from './timeline';
import tracks10 from '../../public/blender/shot10.tracks.json';
import tracks10h from '../../public/blender/shot10h.tracks.json';
import tracksI1 from '../../public/blender/shoti1.tracks.json';

// Animatic v4.0: the approved new structure, cut on the beat grid of the score (see timeline.ts).
// Picture is Blender previz plates + the tactical display; every cut is a whole or half beat.
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ramp = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const out3 = (x: number) => 1 - Math.pow(1 - x, 3);
const smooth = (x: number) => x * x * (3 - 2 * x);

type Tracks = {tracks: Record<string, Record<string, number[]>>};
const track = (tr: Tracks, name: string, blenderFrame: number) => {
  const keys = Object.keys(tr.tracks).map(Number);
  const f = Math.min(Math.max(blenderFrame, Math.min(...keys)), Math.max(...keys));
  const p = tr.tracks[String(f)]?.[name];
  return p ? {x: p[0] * 1920, y: p[1] * 1080} : null;
};

// ---------- plates ----------
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

type ClipProps = {
  src: string; // file in public/blender, without extension
  from?: number; // first source frame
  z?: [number, number]; // zoom at the first and last frame of the cut (a slow push keeps every cut alive)
  o?: [number, number]; // zoom origin, 0..1
  ir?: boolean; // thermal look
  dim?: number; // brightness multiplier (under big type)
};
const Clip: React.FC<ClipProps> = ({src, from = 0, z = [1.02, 1.07], o = [0.5, 0.5], ir, dim = 1}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const zoom = z[0] + (z[1] - z[0]) * (frame / Math.max(1, durationInFrames - 1));
  const filter = `${ir ? 'grayscale(1) contrast(1.15) brightness(1.05) ' : ''}${dim !== 1 ? `brightness(${dim})` : ''}`.trim() || undefined;
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile(`blender/${src}.mp4`)} trimBefore={from} muted
        style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`, transformOrigin: `${o[0] * 100}% ${o[1] * 100}%`, filter}} />
      {ir ? <IRFinish /> : (
        <>
          <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)'}} />
          <AbsoluteFill style={{backgroundImage: `url(${staticFile('v3/grain.png')})`, backgroundSize: '512px 512px', opacity: 0.07, mixBlendMode: 'overlay',
            backgroundPosition: `${Math.floor(random(`gx${frame}`) * 512)}px ${Math.floor(random(`gy${frame}`) * 512)}px`}} />
        </>
      )}
    </AbsoluteFill>
  );
};

// The sensor head (mast with rotating bar) sweeps the horizon, then stops dead on the contact. The overlay makes it read as
// a sensor: a sweep line on a range ring while it searches, a lock mark and "CONTACT" when it stops (source frame 25).
const Sensor: React.FC<{from?: number; z?: [number, number]; dim?: number}> = ({from = 0, z = [1.0, 1.08], dim}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const sf = from + frame; // source frame
  const o: [number, number] = [0.46, 0.42];
  const zoom = z[0] + (z[1] - z[0]) * (frame / Math.max(1, durationInFrames - 1));
  const head = {x: o[0] * 1920 + (0.46 + 0.0016 * sf - o[0]) * 1920 * zoom, y: o[1] * 1080 + (0.425 - o[1]) * 1080 * zoom};
  const k = smooth(clamp(sf / 25));
  const locked = sf >= 25;
  const a = ((-18 - 250 * (1 - k) * (1 - k)) * Math.PI) / 180;
  const RX = 760 * zoom, RY = 150 * zoom;
  const tip = (ang: number, r = 1) => ({x: head.x + Math.cos(ang) * RX * r, y: head.y + Math.sin(ang) * RY * r});
  const end = tip(a);
  const lockK = out3(clamp((sf - 25) / 4));
  const col = locked ? colors.threat : colors.marlin;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Clip src="shots1" from={from} z={z} o={o} dim={dim} />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <ellipse cx={head.x} cy={head.y} rx={RX} ry={RY} fill="none" stroke={colors.marlin} strokeOpacity={0.3} strokeWidth={1.6} strokeDasharray="5 9" />
        {!locked && Array.from({length: 9}, (_, i) => {
          const p = tip(a - (i + 1) * 0.07 * (1 - k * 0.6));
          return <line key={i} x1={head.x} y1={head.y} x2={p.x} y2={p.y} stroke={colors.marlin} strokeOpacity={0.3 * (1 - i / 9)} strokeWidth={3} />;
        })}
        <line x1={head.x} y1={head.y} x2={end.x} y2={end.y} stroke={col} strokeOpacity={0.95} strokeWidth={locked ? 3.4 : 2.6} />
        {locked && (
          <g transform={`translate(${end.x} ${end.y})`} opacity={lockK}>
            <rect x={-11} y={-11} width={22} height={22} fill={colors.threat} transform="rotate(45)" />
            <circle r={26 + 30 * (1 - lockK)} fill="none" stroke={colors.threat} strokeWidth={2.6} />
          </g>
        )}
      </svg>
      <div style={{position: 'absolute', top: 150, left: 110, fontFamily: fonts.mono, fontSize: 24, letterSpacing: '0.16em', color: col, border: `1.5px solid ${col}`,
        padding: '8px 16px', borderRadius: 3, background: 'rgba(8,14,22,0.6)'}}>{locked ? 'SENSOR · CONTACT' : 'SENSOR · SEARCHING'}</div>
    </AbsoluteFill>
  );
};

// ---------- thermal overlay ----------
const irChip: React.CSSProperties = {fontFamily: fonts.mono, fontSize: 20, color: 'rgba(255,255,255,0.88)', letterSpacing: '0.14em'};
const Brackets: React.FC<{cx: number; cy: number; w: number; h: number; k: number; color?: string}> = ({cx, cy, w, h, k, color = 'rgba(255,255,255,0.9)'}) => (
  <g stroke={color} strokeWidth={2.6} fill="none" opacity={k}>
    {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
      const x = cx + sx * (w / 2 + (1 - k) * 40), y = cy + sy * (h / 2 + (1 - k) * 26);
      return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 30} L ${x} ${y} L ${x - sx * 30} ${y}`} />;
    })}
  </g>
);
// Marlin's own infrared view of the go-fast. `tag` adds the contact read-out; `live` marks it as the feed partners see.
const Thermal: React.FC<{from: number; z?: [number, number]; w?: number; h?: number; tag?: boolean; live?: boolean; dim?: number}> = ({from, z = [1, 1.05], w = 1180, h = 420, tag, live, dim}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = out3(ramp(frame / fps, 0.02, 0.22));
  const c = {x: 0.475 * 1920, y: 0.49 * 1080};
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Clip src="shot10_ir" from={from} z={z} o={[0.475, 0.49]} ir dim={dim} />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <g stroke="rgba(255,255,255,0.5)" strokeWidth={2}>
          <line x1={c.x - 30} y1={c.y} x2={c.x + 30} y2={c.y} /><line x1={c.x} y1={c.y - 30} x2={c.x} y2={c.y + 30} />
        </g>
        <Brackets cx={c.x} cy={c.y} w={w} h={h} k={k} />
      </svg>
      <div style={{...irChip, position: 'absolute', top: 92, left: 40}}>MARLIN · IR WHT</div>
      <div style={{...irChip, position: 'absolute', top: 124, left: 40}}>NFOV</div>
      {tag && (
        <div style={{position: 'absolute', left: c.x - 300, top: c.y + h / 2 + 28, width: 600, textAlign: 'center', fontFamily: fonts.mono, fontSize: 26, color: colors.threat,
          letterSpacing: '0.12em', opacity: k, lineHeight: 1.5, textShadow: '0 0 10px rgba(0,0,0,1), 0 0 4px rgba(0,0,0,1)'}}>
          <div>TOI-01 · GO-FAST</div>
          <div>NO NAV LTS · 3 POB</div>
        </div>
      )}
      {live && (
        <div style={{...irChip, position: 'absolute', bottom: 150, left: 110, fontSize: 40, display: 'flex', alignItems: 'center', gap: 18}}>
          <span style={{width: 22, height: 22, borderRadius: 11, background: colors.marlin, opacity: 0.45 + 0.55 * Math.round((Math.sin(frame * 0.5) + 1) / 2)}} />LIVE
        </div>
      )}
    </AbsoluteFill>
  );
};

// The standoff with the live thermal feed inset (top right) and the line of sight from Marlin's mast to the contact.
const Standoff: React.FC<{src: 'shot10' | 'shot10h'; from: number; z?: [number, number]; o?: [number, number]; inset?: boolean; los?: boolean; dim?: number}> =
  ({src, from, z = [1, 1.04], o = [0.5, 0.5], inset, los, dim}) => {
    const frame = useCurrentFrame();
    const {durationInFrames, fps} = useVideoConfig();
    const tr = (src === 'shot10' ? tracks10 : tracks10h) as Tracks;
    const BF = (src === 'shot10' ? 34 : 145) + from + frame;
    const zoom = z[0] + (z[1] - z[0]) * (frame / Math.max(1, durationInFrames - 1));
    const scr = (p: {x: number; y: number} | null) => p && {x: o[0] * 1920 + (p.x - o[0] * 1920) * zoom, y: o[1] * 1080 + (p.y - o[1] * 1080) * zoom};
    const mast = scr(track(tr, 'mast', BF)), toi = scr(track(tr, 'toi', BF));
    const k = out3(ramp(frame / fps, 0.05, 0.4));
    return (
      <AbsoluteFill style={{background: '#000'}}>
        <Clip src={src} from={from} z={z} o={o} dim={dim} />
        {los && mast && toi && (
          <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
            <line x1={mast.x} y1={mast.y} x2={mast.x + (toi.x - mast.x) * k} y2={mast.y + (toi.y - mast.y) * k} stroke={colors.marlin} strokeOpacity={0.9} strokeWidth={2.4} strokeDasharray="9 8" />
            <circle cx={mast.x} cy={mast.y} r={8} fill="none" stroke={colors.marlin} strokeWidth={2.2} />
          </svg>
        )}
        {inset && (
          <div style={{position: 'absolute', right: 64, top: 150, width: 560, height: 315, overflow: 'hidden', borderRadius: 6, border: '2px solid rgba(255,255,255,0.75)',
            boxShadow: '0 10px 40px rgba(0,0,0,0.6)', opacity: out3(ramp(frame / fps, 0, 0.12))}}>
            <div style={{width: 1920, height: 1080, transform: `scale(${560 / 1920})`, transformOrigin: '0 0', position: 'relative'}}>
              <Clip src="shot10_ir" from={96} z={[1.25, 1.3]} o={[0.475, 0.49]} ir />
              <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}><Brackets cx={0.475 * 1920} cy={0.49 * 1080} w={1380} h={500} k={1} /></svg>
              <div style={{...irChip, position: 'absolute', bottom: 44, left: 52, fontSize: 62, display: 'flex', alignItems: 'center', gap: 26}}>
                <span style={{width: 34, height: 34, borderRadius: 17, background: colors.marlin, opacity: 0.45 + 0.55 * Math.round((Math.sin(frame * 0.5) + 1) / 2)}} />LIVE
              </div>
            </div>
          </div>
        )}
      </AbsoluteFill>
    );
  };

// From above: three Marlins take station around the boat. Tracked callouts make the picture read at a glance.
const Isolate: React.FC<{from: number; z?: [number, number]; dim?: number}> = ({from, z = [1.25, 1.32], dim}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const o: [number, number] = [0.45, 0.7]; // keeps the far edge of the sea out of frame
  const zoom = z[0] + (z[1] - z[0]) * (frame / Math.max(1, durationInFrames - 1));
  const at = (name: string) => {
    const p = track(tracksI1 as Tracks, name, from + frame + 1);
    if (!p) return null;
    const q = {x: o[0] * 1920 + (p.x - o[0] * 1920) * zoom, y: o[1] * 1080 + (p.y - o[1] * 1080) * zoom};
    return q.x > 30 && q.x < 1890 && q.y > 30 && q.y < 1050 ? q : null;
  };
  const k = out3(ramp(frame / fps, 0.03, 0.25));
  const toi = at('toi');
  const marlins = ['marlin', 'marlin2', 'marlin3'].map(at);
  const corners = (c: {x: number; y: number}, w: number, h: number, color: string) => (
    <g stroke={color} strokeWidth={3} fill="none">
      {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
        const x = c.x + sx * (w / 2 + (1 - k) * 30), y = c.y + sy * (h / 2 + (1 - k) * 20);
        return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 18} L ${x} ${y} L ${x - sx * 18} ${y}`} />;
      })}
    </g>
  );
  const label: React.CSSProperties = {position: 'absolute', fontFamily: fonts.mono, fontSize: 22, letterSpacing: '0.14em', textShadow: '0 0 10px rgba(0,0,0,1), 0 0 4px rgba(0,0,0,1)', opacity: k};
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Clip src="shoti1" from={from} z={z} o={o} dim={dim} />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}} opacity={k}>
        {toi && marlins.map((m, i) => m && (
          <line key={`l${i}`} x1={m.x} y1={m.y} x2={toi.x} y2={toi.y} stroke={colors.marlin} strokeOpacity={0.55} strokeWidth={2} strokeDasharray="6 9" />
        ))}
        {marlins.map((m, i) => m && <g key={`m${i}`}>{corners(m, 120 * zoom, 84 * zoom, colors.marlin)}</g>)}
        {toi && corners(toi, 250 * zoom, 150 * zoom, colors.threat)}
      </svg>
      {marlins.map((m, i) => m && <div key={`ml${i}`} style={{...label, left: m.x - 60 * zoom, top: m.y - 42 * zoom - 34, color: colors.marlin}}>MARLIN</div>)}
      {toi && <div style={{...label, left: toi.x - 125 * zoom, top: toi.y + 75 * zoom + 10, color: colors.threat}}>TOI-01</div>}
    </AbsoluteFill>
  );
};

// ---------- supers ----------
// Section title: slams in on the downbeat, bottom left, clear of the action.
const Slam: React.FC<{n: string; word: string}> = ({n, word}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const k = out3(clamp(frame / 4));
  const outK = 1 - clamp((frame - (durationInFrames - 4)) / 4);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(4,8,13,0.72) 0%, rgba(4,8,13,0) 46%)', opacity: k * outK}} />
      <div style={{position: 'absolute', left: 110, bottom: 118, opacity: k * outK, transform: `scale(${1.22 - 0.22 * k})`, transformOrigin: '0% 100%', color: colors.white,
        textShadow: '0 4px 30px rgba(0,0,0,0.85)'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 20, fontFamily: fonts.mono, fontSize: 40, color: colors.marlin, letterSpacing: '0.2em'}}>
          <span style={{width: 90 * k, height: 5, background: colors.marlin}} />{n}
        </div>
        <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 190, letterSpacing: '0.1em', lineHeight: 1.05}}>{word}</div>
      </div>
    </AbsoluteFill>
  );
};
// Small section tag that stays for the rest of the section.
const Tag: React.FC<{text: string}> = ({text}) => {
  const [num, ...rest] = text.split(' ');
  return (
    <AbsoluteFill>
      {/* soft shade so the tag reads over spray and glitter */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 640px 250px at 330px 905px, rgba(4,8,13,0.62) 0%, rgba(4,8,13,0) 100%)'}} />
      <div style={{position: 'absolute', left: 110, bottom: 130, fontFamily: fonts.mono, color: colors.white, textShadow: '0 2px 18px rgba(0,0,0,0.85)'}}>
        <div style={{width: 56, height: 3, background: colors.marlin, marginBottom: 16}} />
        <span style={{color: colors.marlin, fontSize: 34, marginRight: 18}}>{num}</span>
        <span style={{fontSize: 48, fontWeight: 500, letterSpacing: '0.2em'}}>{rest.join(' ')}</span>
      </div>
    </AbsoluteFill>
  );
};
const Chip: React.FC<{text: string; top?: number}> = ({text, top = 150}) => (
  <div style={{fontFamily: fonts.mono, fontSize: 22, letterSpacing: '0.14em', color: colors.white, position: 'absolute', top, left: 110, border: `1.5px solid ${colors.white}`,
    padding: '8px 16px', borderRadius: 3, background: 'rgba(8,14,22,0.6)'}}>{text}</div>
);
// The one number in the film, always with its footnote.
const Readout: React.FC = () => {
  const frame = useCurrentFrame();
  const k = out3(clamp(frame / 5));
  return (
    <>
      <div style={{position: 'absolute', right: 110, bottom: 150, opacity: k, transform: `scale(${1.15 - 0.15 * k})`, transformOrigin: '100% 100%', fontFamily: fonts.mono, color: colors.marlin,
        border: `2.5px solid ${colors.marlin}`, borderRadius: 4, padding: '12px 28px', fontSize: 62, fontWeight: 500, letterSpacing: '0.1em', background: 'rgba(8,14,22,0.74)'}}>50 NM · 30 MIN*</div>
      <div style={{position: 'absolute', right: 110, bottom: 100, fontFamily: fonts.mono, fontSize: 22, color: 'rgba(255,255,255,0.85)', textShadow: '0 1px 8px rgba(0,0,0,0.85)', opacity: k}}>*Design target</div>
    </>
  );
};
// The three words, one per bar, each landing on the downbeat.
const WORDS = ['DETECT.', 'ISOLATE.', 'SURVEIL.'];
const BigWord: React.FC<{i: number}> = ({i}) => {
  const frame = useCurrentFrame();
  const k = out3(clamp(frame / 4));
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <AbsoluteFill style={{background: 'rgba(4,8,13,0.34)'}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 250, letterSpacing: '0.09em', paddingLeft: '0.09em', color: colors.white, transform: `scale(${1.55 - 0.55 * k})`,
        opacity: clamp(frame / 2), textShadow: '0 6px 50px rgba(0,0,0,0.9)'}}>{WORDS[i]}</div>
      <div style={{position: 'absolute', bottom: 150, display: 'flex', gap: 40, fontFamily: fonts.mono, fontSize: 30, letterSpacing: '0.26em'}}>
        {WORDS.map((w, j) => (
          <span key={w} style={{color: j === i ? colors.marlin : colors.white, opacity: j <= i ? 1 : 0.28}}>{w}</span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ---------- end card ----------
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;
  const land = (a: number, d = 0.3) => ramp(t, a, a + d);
  const k = out3(clamp(frame / 6));
  const tag = VO.v14 - tk(K.end) + 0.75; // the three words settle under the name once the narrator has said it
  return (
    <AbsoluteFill style={{background: colors.navy, alignItems: 'center', justifyContent: 'center', color: colors.white}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 42%, rgba(79,209,197,0.10) 0%, rgba(0,0,0,0) 55%)'}} />
      <Img src={staticFile('assets/logo/archimedes-white-temp.png')} style={{width: 400, opacity: k}} />
      <div style={{fontFamily: fonts.display, fontWeight: 700, fontSize: 150, letterSpacing: '0.3em', paddingLeft: '0.3em', marginTop: 34, opacity: clamp(frame / 2), transform: `scale(${1.12 - 0.12 * k})`}}>MARLIN</div>
      <div style={{fontFamily: fonts.mono, fontSize: 40, letterSpacing: '0.14em', marginTop: 10, opacity: land(tag)}}>Detect. Isolate. Surveil.</div>
      <div style={{width: 140 * land(tag + 0.3), height: 4, background: colors.threat, margin: '38px 0'}} />
      <div style={{fontFamily: fonts.mono, fontSize: 26, color: colors.steel, letterSpacing: '0.12em', opacity: land(tag + 0.3)}}>{CONTACT_V4}</div>
      <div style={{position: 'absolute', bottom: 56, fontFamily: fonts.mono, fontSize: 17, color: colors.steel, maxWidth: 1500, textAlign: 'center', opacity: 0.9 * land(0.2)}}>{DISCLAIMER_V4}</div>
      <AbsoluteFill style={{background: '#000', opacity: clamp((frame - (durationInFrames - 10)) / 9)}} />
    </AbsoluteFill>
  );
};

// ---------- review slate ----------
const Slate: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const sec = SECTIONS.find((s) => frame >= (s.k0 < 0 ? 0 : fk(s.k0)) && frame < fk(s.k1)) ?? SECTIONS[SECTIONS.length - 1];
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
        <div style={{...chip, fontSize: 15, padding: '6px 12px'}}>{sec.n} · {sec.name.toUpperCase()}</div>
      </div>
      <div style={{position: 'absolute', top: 30, left: 32, ...chip, fontSize: 15, padding: '6px 12px', opacity: 0.85}}>
        ARCHIMEDES FREIGHT · MARLIN · CONCEPT VISUALIZATION · 3D PREVIZ · NOT FINAL
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 32, ...chip, fontSize: 18}}>TC {tc}</div>
    </AbsoluteFill>
  );
};

// ---------- display cameras (film time in seconds) ----------
const C0 = contactAt(0);
const push = (t: number, k0: number, k1: number) => ramp(t, tk(k0), tk(k1));
const camTag = (t: number): Camera => ({cx: C0.x + 60, cy: C0.y + 40, k: 3.1 - 0.5 * out3(push(t, 24, 26))}); // tight on the contact as it is tagged
const camNearest = (t: number): Camera => ({cx: 1085, cy: 492, k: 1.3 + 0.07 * push(t, 26, 28)}); // wide enough for all three reach rings
const camVectors = (t: number): Camera => ({cx: 1085, cy: 492, k: 1.5 + 0.1 * push(t, 30, 32)});
const camClose1 = (t: number): Camera => ({cx: 1100, cy: 480, k: 1.75 + 0.15 * push(t, 42, 44)});
const camClose2 = (t: number): Camera => ({cx: contactAt(t).x - 20, cy: contactAt(t).y + 30, k: 2.3 + 0.25 * push(t, 48, 50)});
const camBox = (t: number): Camera => ({cx: contactAt(t).x - 10, cy: contactAt(t).y + 20, k: 3.0 + 0.25 * push(t, 54, 56)});
const camPartner1 = (t: number): Camera => ({cx: contactAt(t).x + 340, cy: contactAt(t).y + 30, k: 1.28 + 0.06 * push(t, 66, 68)});
const camPartner2 = (t: number): Camera => {
  const c = contactAt(t), p = partnerAt(t);
  return {cx: (c.x + p.x) / 2, cy: (c.y + p.y) / 2 + 10, k: 1.85 + 0.1 * push(t, 74, 76)};
};
const camCover = (t: number): Camera => {
  const k = smooth(push(t, 80, 83.2));
  const c = contactAt(t);
  return {cx: c.x + 200 + (960 - c.x - 200) * k, cy: c.y + 40 + (540 - c.y - 40) * k, k: 1.7 - 0.7 * k};
};

// ---------- the cut ----------
type Cut = [k0: number, k1: number, el: React.ReactNode, name: string];
const map = (k0: number, camera: (t: number) => Camera) => <Map start={fk(k0) / 24} camera={camera} />;
const CUTS: Cut[] = [
  // 01 · The boat (hook): loud, close, eight beats. Then it is gone.
  [0, 4, <Clip src="shot01" from={0} z={[1.04, 1.1]} o={[0.5, 0.55]} />, 'go-fast: bow and spray'],
  [4, 6, <Clip src="shot01" from={52} z={[1.2, 1.3]} o={[0.2, 0.4]} />, 'go-fast: the crew'],
  [6, 8, <Clip src="shot01" from={66} z={[1.7, 1.9]} o={[0.16, 0.36]} />, 'go-fast: punch in'],
  // 02 · Marlin waits: the apex predator. Near silence, a slow pulse.
  [8, 12, <Clip src="shot06" from={0} z={[1.0, 1.07]} o={[0.62, 0.56]} />, 'Marlin on station, wide'],
  [12, 16, <Clip src="shot06b" from={0} z={[1.0, 1.06]} o={[0.5, 0.45]} />, 'predator close-up'],
  [16, 20, <Clip src="shot06b" from={26} z={[1.5, 1.64]} o={[0.52, 0.42]} />, 'predator, tighter'],
  [20, 22, <Sensor from={0} z={[1.0, 1.08]} />, 'sensor sweeps and stops'],
  [22, 23, <Thermal from={20} z={[1.0, 1.03]} />, 'thermal glimpse'],
  [23, 23.5, <Sensor from={32} z={[1.5, 1.56]} />, 'sensor locked'],
  [23.5, 24, <Thermal from={34} z={[1.7, 1.75]} w={1500} h={640} />, 'thermal, tight'],
  // 03 · Detect
  [24, 26, map(24, camTag), 'display: contact tagged'],
  [26, 28, map(26, camNearest), 'display: the three nearest light up'],
  [28, 30, <Clip src="shotf1" from={8} z={[1.0, 1.09]} o={[0.5, 0.5]} />, 'fan comes alive'],
  [30, 32, map(30, camVectors), 'display: three vectors'],
  [32, 33, <Clip src="shot07" from={26} z={[1.3, 1.36]} o={[0.3, 0.55]} />, 'lift: spray'],
  [33, 34, <Clip src="shot07" from={46} z={[1.0, 1.05]} o={[0.4, 0.6]} />, 'lift: onto the foil'],
  [34, 35, <Clip src="shot07" from={62} z={[1.0, 1.06]} o={[0.55, 0.6]} />, 'lift: pass'],
  [35, 36, <Clip src="shotk1" from={6} z={[1.0, 1.08]} o={[0.5, 0.6]} />, 'strut slicing the surface'],
  // 04 · Isolate: full power, a cut on every beat
  [36, 38, <Clip src="shotv1" from={40} z={[1.0, 1.08]} o={[0.5, 0.6]} />, 'three Marlins vectoring in'],
  [38, 39, <Clip src="shot09" from={20} z={[1.0, 1.05]} o={[0.45, 0.55]} />, 'the run'],
  [39, 40, <Clip src="shotr2" from={12} z={[1.1, 1.2]} o={[0.52, 0.6]} />, 'head-on'],
  [40, 42, <Clip src="shott1" from={0} z={[1.0, 1.08]} />, 'top-down'],
  [42, 44, map(42, camClose1), 'display: closing'],
  [44, 45, <Clip src="shotk1" from={22} z={[1.12, 1.2]} o={[0.5, 0.65]} />, 'strut'],
  [45, 46, <Clip src="shot09" from={90} z={[1.5, 1.58]} o={[0.42, 0.5]} />, 'the run, tight'],
  [46, 47, <Clip src="shotv1" from={78} z={[1.25, 1.32]} o={[0.45, 0.62]} />, 'vectoring, closer'],
  [47, 48, <Clip src="shot01" from={58} z={[1.45, 1.52]} o={[0.2, 0.4]} />, 'the boat, unaware'],
  [48, 50, map(48, camClose2), 'display: almost there'],
  [50, 51, <Clip src="shotr2" from={26} z={[1.0, 1.1]} o={[0.52, 0.6]} />, 'head-on, close'],
  [51, 52, <Clip src="shott1" from={36} z={[1.25, 1.33]} />, 'top-down, tight'],
  [52, 54, <Isolate from={28} z={[1.25, 1.32]} />, 'three Marlins take station around the boat'],
  [54, 56, map(54, camBox), 'display: the box closes'],
  // eyes on: the score drops out; we are inside the sensor
  [56, 58, <Thermal from={30} z={[1.0, 1.04]} tag />, 'thermal: contact held'],
  [58, 60, <Thermal from={78} z={[1.45, 1.55]} w={1500} h={640} tag />, 'thermal: three persons on board'],
  // 05 · Surveil: heavy, controlled
  [60, 62, <Standoff src="shot10" from={46} z={[1.0, 1.05]} o={[0.3, 0.6]} />, 'off the foil at standoff'],
  [62, 64, <Standoff src="shot10" from={80} z={[1.0, 1.04]} o={[0.4, 0.6]} inset />, 'standoff + live feed'],
  [64, 66, <Isolate from={54} z={[1.3, 1.38]} />, 'on station, from above'],
  [66, 68, map(66, camPartner1), 'display: partner en route'],
  [68, 70, <Thermal from={110} z={[1.25, 1.32]} w={1300} h={520} live />, 'thermal: live'],
  [70, 72, <Standoff src="shot10h" from={0} z={[1.0, 1.04]} o={[0.4, 0.6]} los />, 'standoff: line of sight'],
  [72, 74, <Clip src="shot06b" from={40} z={[1.18, 1.26]} o={[0.5, 0.45]} />, 'it stays'],
  [74, 76, map(74, camPartner2), 'display: partner closing'],
  [76, 78, <Standoff src="shot10h" from={30} z={[1.3, 1.38]} o={[0.22, 0.62]} />, 'standoff, tight'],
  [78, 78.5, <Thermal from={124} z={[1.6, 1.64]} w={1500} h={640} />, 'flash: thermal'],
  [78.5, 79, <Isolate from={72} z={[1.5, 1.55]} />, 'flash: above'],
  [79, 79.5, <Standoff src="shot10h" from={50} z={[1.7, 1.75]} o={[0.75, 0.55]} />, 'flash: the boat'],
  [79.5, 80, map(79.5, camPartner2), 'flash: display'],
  // 06 · Coverage, then the three words: one bar each, cuts doubling in speed
  [80, 84, map(80, camCover), 'display: the fleet re-spaces'],
  [84, 85, <Sensor from={14} z={[1.1, 1.16]} dim={0.75} />, 'DETECT: sensor'],
  [85, 86, <Thermal from={40} z={[1.2, 1.25]} dim={0.75} />, 'DETECT: thermal'],
  [86, 87, <Clip src="shot06b" from={10} z={[1.7, 1.76]} o={[0.52, 0.4]} dim={0.75} />, 'DETECT: mast'],
  [87, 88, <Thermal from={60} z={[1.8, 1.86]} w={1500} h={640} dim={0.75} />, 'DETECT: thermal tight'],
  [88, 88.5, <Clip src="shotv1" from={50} z={[1.05, 1.08]} o={[0.5, 0.6]} dim={0.75} />, 'ISOLATE 1'],
  [88.5, 89, <Clip src="shotr2" from={20} z={[1.15, 1.2]} o={[0.52, 0.6]} dim={0.75} />, 'ISOLATE 2'],
  [89, 89.5, <Clip src="shott1" from={14} z={[1.1, 1.14]} dim={0.75} />, 'ISOLATE 3'],
  [89.5, 90, <Clip src="shot09" from={60} z={[1.2, 1.24]} o={[0.45, 0.55]} dim={0.75} />, 'ISOLATE 4'],
  [90, 90.5, <Clip src="shotk1" from={12} z={[1.1, 1.14]} o={[0.5, 0.65]} dim={0.75} />, 'ISOLATE 5'],
  [90.5, 91, <Isolate from={44} z={[1.25, 1.29]} dim={0.75} />, 'ISOLATE 6'],
  [91, 91.5, <Clip src="shotv1" from={84} z={[1.35, 1.39]} o={[0.45, 0.62]} dim={0.75} />, 'ISOLATE 7'],
  [91.5, 92, <Isolate from={74} z={[1.4, 1.44]} dim={0.75} />, 'ISOLATE 8'],
  [92, 96, <Standoff src="shot10h" from={14} z={[1.0, 1.1]} o={[0.4, 0.6]} dim={0.8} />, 'SURVEIL: it holds'],
];

type Super = [k0: number, k1: number, el: React.ReactNode, name: string];
const SUPERS: Super[] = [
  [8, 20, <Tag text="MARLIN ON STATION" />, 'tag: Marlin on station'],
  [24, 26, <Slam n="01" word="DETECT" />, 'slam 01 DETECT'],
  [26, 36, <Tag text="01 DETECT" />, 'tag 01'],
  [36, 38, <Slam n="02" word="ISOLATE" />, 'slam 02 ISOLATE'],
  [38, 60, <Tag text="02 ISOLATE" />, 'tag 02'],
  [42, 48, <Readout />, '50 NM · 30 MIN* + footnote (on screen with the line)'],
  [60, 62, <Slam n="03" word="SURVEIL" />, 'slam 03 SURVEIL'],
  [62, 80, <Tag text="03 SURVEIL" />, 'tag 03'],
  [66, 68, <Chip text="PARTNER EN ROUTE" />, 'chip: partner en route'],
  [74, 76, <Chip text="PARTNER CLOSING" />, 'chip: partner closing'],
  [80, 84, <Chip text="FLEET RE-SPACES · COVERAGE HOLDS" />, 'chip: coverage'],
  [84, 88, <BigWord i={0} />, 'DETECT.'],
  [88, 92, <BigWord i={1} />, 'ISOLATE.'],
  [92, 96, <BigWord i={2} />, 'SURVEIL.'],
];

// Flash and shake on the hits of the sound design.
const useHit = () => {
  const frame = useCurrentFrame();
  let flash = 0, dx = 0, dy = 0;
  HITS.forEach(([k, a]) => {
    const d = frame - fk(k);
    if (d >= 0 && d < 5) flash = Math.max(flash, a * 0.5 * (1 - d / 5));
    if (d >= 0 && d < 10) {
      const amp = a * 11 * Math.pow(1 - d / 10, 2);
      dx += amp * Math.sin(d * 2.4 + k);
      dy += amp * Math.cos(d * 3.1 + k * 1.7);
    }
  });
  return {flash, dx, dy};
};

export const MarlinV4: React.FC<{slate?: boolean}> = ({slate = true}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const {flash, dx, dy} = useHit();
  const seq = ([k0, k1, el, name]: Cut | Super, i: number, pre = '') => (
    <Sequence key={`${pre}${i}`} from={fk(k0)} durationInFrames={fk(k1) - fk(k0)} name={`${pre}${k0}-${k1} ${name}`}>{el}</Sequence>
  );
  const fadeOut = clamp((frame - fk(94.4)) / (fk(96) - 2 - fk(94.4))); // down to black under the swell into the end card
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{transform: `translate(${dx}px, ${dy}px) scale(1.014)`}}>
        {CUTS.map((c, i) => seq(c, i))}
        {SUPERS.map((s, i) => seq(s, i, 'super '))}
        {frame < fk(K.end) && <AbsoluteFill style={{background: '#000', opacity: fadeOut}} />}
        <Sequence from={fk(K.end)} durationInFrames={durationInFrames - fk(K.end)} name="07 End card"><EndCard /></Sequence>
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
      {/* sound: score + designed effects + narrator on the same beat grid, mixed and mastered by scripts/build_audio_v4.py */}
      <Audio src={staticFile('audio/v4/mix.flac')} />
      {slate && <Slate />}
    </AbsoluteFill>
  );
};
