# Marlin v5.0: hand-off files

The film: `review/marlin-animatic-v5.0.mp4` (1920x1080, 24 fps, 60 s), Storyboard V7. What changed and why:
`docs/v5-storyboard-v7.md`.

## `reference/`: clean 3D plates of the new shots (Act 3, the stop)

1280x720, 24 fps, no sound, no graphics. Camera move and blocking reference for the video model. In the animatic, shots 11
and 12 play at 0.87x to fill their storyboard length. The plates for shots 01, 05 and 07 are in `review/v3/reference/`.

| File | Shot | What happens |
|---|---|---|
| `09_pass_overhead_plate` | 09 Pass | Overhead drone. The lead Marlin lifts back onto its foils, passes the go-fast wide and cuts in ahead on the same heading; the flank Marlin holds hull-borne. |
| `10_net-away_overhead_plate` | 10 Net away | Overhead. Running directly ahead, the lead Marlin fires the net back from its stern at 0.9 s; two legs fly out and land in a V (point on the track ahead, ends past the bow on both sides); Marlin peels off. |
| `11_fouled_swerve-into-the-net_plate` | 11 Fouled | High side view. Inside the V, the go-fast swerves hard to starboard, runs over the near leg, the props catch it at 1.38 s, the bow drops and it slews to a stop with the net dragged into its stern. |
| `11_fouled_underwater-prop-cutaway_plate` | 11 Fouled (inset) | Under the stern: the net streams in, wraps the lower units and the props stop (slowed down for readability). |
| `12_hold_partner-closing_plate` | 12 Hold | Low and wide. The go-fast dead in the water, the crew standing, the net in its props; the lead Marlin in the foreground and the second beyond, both hull-borne; the partner closing on the horizon. |

Blender scenes: `blender/scenes/shot{p1,n1,x1,h1,u1}.blend`. Blockout models: proportions and motion are the reference,
not surface detail. The net (a floated head rope) and the launcher (two tubes on the after body) are notional.

## `audio/`

| File | What |
|---|---|
| `marlin-v5.0_mix.wav` | Final master, 48 kHz stereo, -14 LUFS |
| `marlin-v5.0_stem_music.flac` | Score only, with its sink, silences, build and stop |
| `marlin-v5.0_stem_sfx.flac` | Sound design only |
| `marlin-v5.0_stem_vo.flac` | Narration only (voice: Callum) |

Beat grid: 104 BPM, first beat at 0.055 s. Shot starts are on beats; see `src/v5/timeline.ts`.
