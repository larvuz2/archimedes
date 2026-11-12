# Marlin — 60s concept video

**Client:** Archimedes Freight, Inc. · **Production:** Phatty Acid, Inc. · **Tagline:** Speed is security.

The video is built in code with [Remotion](https://www.remotion.dev) (React → MP4). Remotion is the master
timeline: motion graphics, HUD overlays, maps, titles and the end card are built here, and 3D / stock
footage plates are dropped in as layers.

## Quick start

```bash
npm install
npm run studio        # live preview + scrubbing at http://localhost:3000
npm run render:draft  # half-res 60s draft -> out/marlin-draft.mp4
npm run render        # full 1920x1080 30fps -> out/marlin.mp4
```

## Animatic v2.0 (client Storyboard V5): current

Review file: `review/marlin-animatic-v2.0.mp4`. Code: `src/v2/` (composition `Marlin`; v1 kept as `MarlinV1`).
Fix-by-fix log: `docs/v2-client-fixes.md`. Render + master audio: `npm run master`.

- Frames: `python3 scripts/generate_frames.py` (now V5: gray Marlin, one continuous night) → `public/frames/v2/`
- Gray product reference: `python3 scripts/make_gray_reference.py`
- SFX: `python3 scripts/generate_sfx.py` · Score: `python3 scripts/generate_music.py` and `--act2`
- Tactical display (COP), radar and IR overlays are code: `src/v2/COP.tsx`, `Radar.tsx`, `IRView.tsx`, geometry in `geo.ts`

## Animatic v1.0 (script v2)

Review file: `review/marlin-animatic-v1.0.mp4` (1080p, 60s, with "ANIMATIC v1.0" slate). Remove the slate for
finals with `<Marlin slate={false} />`.

All generation runs through fal.ai (needs `FAL_KEY`):

```bash
python3 scripts/generate_vo.py        # narrator: ElevenLabs v3, voice Brian, lines + direction in src/vo.json
python3 scripts/generate_music.py     # score: ElevenLabs Music, section plan locked to the edit
python3 scripts/generate_frames.py    # storyboard frames: GPT Image 2.5 (openai/gpt-image-2.5/flare/edit)
python3 scripts/generate_frames.py --only f07   # redo one frame
```

- **Frames** share one cinematography block and one product description; the Marlin reference sheet
  (`public/assets/models/marlin-reference-sheet.jpg`) is attached to every generation, plus earlier frames
  where boats must match (`CONTINUITY`). Exact prompts: `docs/frames/prompts/`.
- **Music level** is automated in `src/audio.ts`: ducked under VO, almost gone under
  "Archimedes Freight presents... Marlin", then swells to full right after "Marlin".
- **Timing**: `src/timeline.ts` (shots, supers, VO start times).

## Layout

| Path | What |
|---|---|
| `src/timeline.ts` | Shot list, timings, VO, on-screen text, sound notes (from Storyboard V3). Single source of truth. |
| `src/theme.ts` | Colors / fonts / format. Replace with the Archimedes brand guide when we have it. |
| `src/Marlin.tsx` | Master edit: frames, supers, end card, music + VO, slate. |
| `src/components/` | FrameShot (camera moves), Supers, EndCard, AnimaticSlate. |
| `public/frames/` | GPT Image 2.5 storyboard frames f01–f12. |
| `public/assets/` | Logo, footage, 3D models (`.glb`), HDRIs. |
| `public/audio/` | VO, music, SFX. |
| `public/fonts/` | Bundled fonts (renders never hit the network). |
| `public/storyboard/` | The 11 storyboard sketches (shown in the animatic). |
| `docs/storyboard-frames.md` | Composition notes for every sketch: framing, colors, labels, what must carry into production. |
| `docs/reference/` | Storyboard PDF, extracted frames, contact sheet. |
| `scripts/` | `extract_storyboard_frames.py` pulls the sketches out of the PDF. |
| `docs/` | Creative approach, asset checklist. |

## Render notes

- Cloud sandbox has no GPU: 3D uses software WebGL (`swangle`, set in `remotion.config.ts`). Fine for
  stylized 3D; photoreal ocean / spray should be rendered on a GPU machine (Blender or Unreal) and imported as plates.
- Animatic render: ~35s for the full 60s at half res on 4 cores.
