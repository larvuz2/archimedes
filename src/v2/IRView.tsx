import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {colors, fonts} from '../theme';

// Thermal camera view with a generic sensor overlay (no models, bands or ranges).
// `target` = where the boat sits in the image (% of frame); the view slews onto it.
export const IRView: React.FC<{src: string; target: {x: number; y: number}; tag?: string[]; tagPos?: {left: number; top: number}; super?: string; readout?: string; slew?: boolean}> =
  ({src, target, tag, tagPos = {left: 300, top: 760}, super: sup, readout, slew = true}) => {
    const frame = useCurrentFrame();
    const {fps} = useVideoConfig();
    const k = slew ? Easing.bezier(0.2, 0.8, 0.2, 1)(Math.min(1, frame / (0.9 * fps))) : 1;
    const zoom = 1.3;
    // translate so the target lands near screen center (clamped so the image always fills the frame),
    // starting off-target for the slew
    const lim = ((zoom - 1) / 2) * 100 / zoom;
    const cl = (v: number) => Math.max(-lim, Math.min(lim, v));
    const tx = cl((50 - target.x) + (1 - k) * 10);
    const ty = cl((50 - target.y) + (1 - k) * -7);
    const jitterX = (random(`jx${frame}`) - 0.5) * 0.15, jitterY = (random(`jy${frame}`) - 0.5) * 0.15;
    const settle = interpolate(frame, [0.7 * fps, 1.1 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const chip: React.CSSProperties = {fontFamily: fonts.mono, fontSize: 20, color: 'rgba(255,255,255,0.85)', letterSpacing: '0.14em'};
    return (
      <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
        <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(1) contrast(1.08)',
          transform: `scale(${zoom}) translate(${tx + jitterX}%, ${ty + jitterY}%)`}} />
        {/* sensor noise + vignette */}
        <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
        <AbsoluteFill style={{opacity: 0.06, backgroundImage: `repeating-linear-gradient(0deg, #fff 0 1px, transparent 1px 3px)`}} />
        <div style={{...chip, position: 'absolute', top: 92, left: 40}}>IR WHT</div>
        <div style={{...chip, position: 'absolute', top: 92, right: 40}}>NFOV</div>
        {/* center reticle */}
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
          <g stroke="rgba(255,255,255,0.85)" strokeWidth={2.5} fill="none" opacity={0.5 + settle * 0.5}>
            {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
              const d = 230 - settle * 40, h = 130 - settle * 20;
              const x = 960 + sx * d, y = 540 + sy * h;
              return <path key={`${sx}${sy}`} d={`M ${x} ${y - sy * 34} L ${x} ${y} L ${x - sx * 34} ${y}`} />;
            })}
            <line x1={940} y1={540} x2={980} y2={540} /><line x1={960} y1={520} x2={960} y2={560} />
          </g>
        </svg>
        {tag && (
          <div style={{position: 'absolute', left: tagPos.left, top: tagPos.top, fontFamily: fonts.mono, fontSize: 24, color: colors.threat,
            letterSpacing: '0.12em', opacity: settle, lineHeight: 1.5, background: 'rgba(0,0,0,0.6)', padding: '8px 14px', borderLeft: `3px solid ${colors.threat}`}}>
            {tag.map((l) => <div key={l}>{l}</div>)}
          </div>
        )}
        {readout && <div style={{...chip, position: 'absolute', bottom: 90, left: 40, fontSize: 18}}>{readout}</div>}
        {sup && (
          <div style={{position: 'absolute', left: 110, bottom: 130, fontFamily: fonts.mono, color: colors.white, opacity: settle}}>
            <span style={{color: colors.marlin, fontSize: 34, marginRight: 18}}>{sup.split(' ')[0]}</span>
            <span style={{fontSize: 48, fontWeight: 500, letterSpacing: '0.2em'}}>{sup.split(' ').slice(1).join(' ')}</span>
          </div>
        )}
      </AbsoluteFill>
    );
  };
