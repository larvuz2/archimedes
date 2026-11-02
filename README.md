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

## Narrator (scratch VO)

Generated through fal.ai with ElevenLabs multilingual v2, voice **Brian** (deep, calm American read), at 1.1x speed.
Needs `FAL_KEY` in the environment.

```bash
python3 scripts/generate_vo.py                # regenerate all 11 lines
python3 scripts/generate_vo.py --only 5 7     # just some shots
python3 scripts/generate_vo.py --voice Bill   # try another voice
python3 scripts/generate_vo.py --audition     # same line in 6 voices -> public/audio/vo/auditions/
```

Line start times live in `src/timeline.ts` (`voAt`). Shots were retimed from the storyboard so the VO fits (see the comments there).

## Layout

| Path | What |
|---|---|
| `src/timeline.ts` | Shot list, timings, VO, on-screen text, sound notes (from Storyboard V3). Single source of truth. |
| `src/theme.ts` | Colors / fonts / format. Replace with the Archimedes brand guide when we have it. |
| `src/Marlin.tsx` | Master edit. Each shot is a `<Sequence>`; currently placeholder animatic cards. |
| `src/shots/` | One component per shot as they're built. `ThreeSmokeTest` proves 3D renders. |
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
