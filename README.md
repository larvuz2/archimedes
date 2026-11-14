# Marlin — 60s concept video

**Client:** Archimedes Freight, Inc. · **Production:** Phatty Acid, Inc. · **Tagline:** Detect. Isolate. Surveil.

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

## Animatic v4.0 (approved new structure, cut to the score): current

Review file: `review/marlin-animatic-v4.0.mp4` (24 fps, 62 shots, every cut on a beat of the 104 BPM score).
What the client's reference film does and how v4 applies it: `docs/v4-reference-and-cut.md`.
New clean 3D plates: `review/v4/reference/`. Audio stems (score, effects, voice, mix): `review/v4/audio/`.

| Part | Where | How to rebuild |
|---|---|---|
| Edit | `src/v4/MarlinV4.tsx` (cut list in beats), `src/v4/timeline.ts` (beat grid), `src/v4/Map.tsx` (tactical display) | `npx remotion render src/index.ts Marlin review/marlin-animatic-v4.0.mp4 --crf=18` |
| New 3D shots | `blender/previz.py`: `06b v1 i1 s1 f1 k1 r2 t1 10h` | `blender/render_v4.sh && blender/render_v4b.sh` |
| Score | `scripts/generate_music_v4.py` (ElevenLabs Music, bar plan at 104 BPM) | `python3 scripts/generate_music_v4.py 3 1` |
| Narration | `scripts/generate_vo_v4.py` (14 short lines, voice Brian) | `python3 scripts/generate_vo_v4.py` |
| Effects | `scripts/generate_sfx_v4.py` (14 sources) + synthesized hits, pulses, pings | `python3 scripts/generate_sfx_v4.py` |
| Mix + master | `scripts/build_audio_v4.py` (everything on the beat grid; Pedalboard master, -14 LUFS) | `/opt/venv-audio/bin/python scripts/build_audio_v4.py` |
| Quick look | `scripts/contact_sheet.mjs` (stills at chosen frames or beats, one bundle) | `node scripts/contact_sheet.mjs out/stills k24,k36,k60` |

The audio tools also need `pedalboard`. v3 is still in the project as composition `MarlinV3`.

## Animatic v3.0 (Storyboard V5, Blender previz)

Review file: `review/marlin-animatic-v3.0.mp4` (24 fps). Shot-by-shot check against the storyboard: `docs/v3-shot-checklist.md`.
Clean reference clips per shot (for the video model): `review/v3/reference/`.

| Part | Where | How to rebuild |
|---|---|---|
| 3D shots 01, 03, 06, 07, 09, 10 | `blender/previz.py` (models, ocean, light, spray, cameras), scenes in `blender/scenes/*.blend` | `blender/render_all.sh` (Cycles on CPU; resumable). One frame: `python blender/previz.py --shot 07 --still 2.0` |
| 2D shots 02, 04, 05, 08, 11, 12 | `src/v3/` (Radar, COP, end card) | part of the Remotion render |
| Sound | `scripts/build_audio_v3.py` (all effects synthesized; score + narrator arranged and mastered) | `/opt/venv-audio/bin/python scripts/build_audio_v3.py` |
| Sound QC | `scripts/audio_qc.py` (AudioSet classifier: flags speech/scream-like sound) | `python scripts/audio_qc.py public/audio/v3/sfx.wav public/audio/v3/music.wav` |
| Edit | `src/v3/MarlinV3.tsx`, timings in `src/v3/timeline.ts` | `npx remotion render src/index.ts MarlinV3 review/marlin-animatic-v3.0.mp4` |

Blender is used as a Python module (`pip install bpy==5.3.0` in a venv); the audio tools need `torch transformers soundfile librosa scipy`.

## Animatic v2.0 (client Storyboard V5)

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
