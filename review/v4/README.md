# Marlin v4.0: hand-off files

The film: `review/marlin-animatic-v4.0.mp4` (1920x1080, 24 fps, 60 s). How it was built and why:
`docs/v4-reference-and-cut.md`.

## `reference/`: clean 3D plates of the new shots

1280x720, 24 fps, no sound, no graphics, no slate. Camera move and blocking reference for the video model.
The v3 plates (`review/v3/reference/`) are still used for the go-fast, the loiter, the lift, the run and the thermal view.

| File | Used for | What the camera does |
|---|---|---|
| `marlin-waits_predator-close-up_plate` | Marlin waits | Low, close, off the bow. Duct and sensor mast against the moon. Slow drift. 3.5 s |
| `detect_sensor-sweeps-and-stops_plate` | Detect | Extreme close-up of the sensor head against the sky. The bar sweeps, then stops dead at 1.05 s. |
| `detect_fan-comes-alive_plate` | Detect | Close on the duct. Blades go from still to a blur; first spray. |
| `isolate_three-marlins-vectoring-in_plate` | Isolate | Drone above and behind the nearest Marlin; two more converge ahead on the moon path. 4 s |
| `isolate_strut-slicing-the-surface_plate` | Isolate | Low, tracking, at the waterline: the foil strut cutting the surface at speed. |
| `isolate_head-on_plate` | Isolate | Locked low on the water; the Marlin comes straight at the lens on its foil. |
| `isolate_top-down_plate` | Isolate | Straight down from a drone: one Marlin at speed, wake drawing a line. |
| `isolate_taking-station_from-above_plate` | Isolate / Surveil | High three-quarter view: three Marlins take station ahead of the go-fast and on both flanks. 3.5 s |
| `surveil_standoff-hold_plate` | Surveil | Continues the v3 standoff shot: Marlin hull-borne in the foreground, pacing the boat; second Marlin beyond. 3 s |

Blender scenes: `blender/scenes/*.blend`. Blockout models: proportions and motion are the reference, not surface detail.

## `audio/`: the soundtrack, to lay under any picture cut to the same timing

| File | What |
|---|---|
| `marlin-v4.0_mix.wav` | Final master, 48 kHz stereo, -14 LUFS, true peak -1.3 dBFS |
| `marlin-v4.0_stem_music.flac` | Score only (already ducked under the narration) |
| `marlin-v4.0_stem_sfx.flac` | Sound design only |
| `marlin-v4.0_stem_vo.flac` | Narration only |

The stems are at their level in the mix but before the master (level ride, compression, limiter), so their sum is close
to the final mix, not identical. All four start at 0:00 of the film.

Beat grid of the score: 104 BPM, first beat at 0.345 s. Section downbeats: 0:14.19 DETECT, 0:21.11 ISOLATE,
0:34.96 SURVEIL, 0:48.81 / 0:51.11 / 0:53.42 the three words, 0:55.73 end card.
