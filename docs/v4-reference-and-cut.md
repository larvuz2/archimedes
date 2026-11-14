# Animatic v4.0: what the reference does, and how Marlin now does it

Client feedback on the new-structure PDF (13 Nov): *"It looks on point now to me. Need to build momentum and power, so the
video has a sense of urgency."* On the reference film: *"Take the tone / intensity, momentum, powerful / aggressive music,
build, and apply to Marlin."*

So v4 keeps the approved structure and wording and changes how it moves and sounds.

## The reference, measured

Frame-by-frame and sample-by-sample analysis of the 59.8 s reference (a special-operations recruiting film).

| | Reference | Animatic v3.0 | Animatic v4.0 |
|---|---|---|---|
| Shots | 75 | 12 | 62 |
| Median shot | 0.6 s | 4.5 s | 0.58 s |
| Pace | accelerates: 1.2 s, then 0.6 s, then 0.3 s at the end | constant | accelerates: 2.3 s, then 1.2 s, then 0.6 s, then 0.3 s |
| Cuts on the beat | yes, 103 BPM | no | yes, 104 BPM, every cut on a beat or half beat |
| Music | dark hybrid trailer score, rhythm-driven, no melody, never stops | ambient bed | original score in the same tempo and energy |
| Loudness | -14.0 LUFS; rises from -17 to -12 (short-term) | -13.9 LUFS | -13.9 LUFS; rises from -19 to -11 (short-term) |
| Narration | 47 words, short declaratives and triads | 4 long lines | 46 words in 14 short lines, ends on the triad |
| Ending | drop-out, biggest hit on the emblem, held | fade | drop-out, biggest hit on the name, held |

What makes the reference feel urgent:

1. **It never rests.** Sound is wall to wall (never below -30 dB) and a cut lands on almost every beat.
2. **It starts low and dark and ends bright and loud.** Level and picture brightness both rise through the film.
3. **Hits mark the turns.** A triple hit at 0:06, a drop-out at 0:28 before the last act, the biggest hit at 0:56 as the emblem lands.
4. **The voice is calm.** Low, slow, certain, over fast picture. The contrast is the power.
5. **Details, not coverage.** Silhouettes, backlight, water, macro shots of equipment; almost no wide establishing shots.
6. **Three-part lines.** "By air, by sea, by land." "One force, one mission, one standard."

## How v4 applies it

Everything is placed on the beat grid of the score: `t(k) = 0.345 + k * 60/104` seconds (`src/v4/timeline.ts`,
`scripts/build_audio_v4.py`).

| Time | Beats | Section | Picture | Sound |
|---|---|---|---|---|
| 0:00 | 0 to 8 | The boat | go-fast, close and loud, three cuts | engine roar, hit on the first frame, sucked out on the cut |
| 0:05 | 8 to 20 | Marlin waits | wide, then the predator close-up on the second hit, then tighter | near silence: sea, a slow heartbeat pulse |
| 0:12 | 20 to 24 | (turn) | sensor head sweeps and stops, thermal glimpse, stutter | servo, riser into the slam |
| 0:14 | 24 to 36 | **01 DETECT** | contact tagged, the three nearest light up on the beat, fan, vectors, lift in three jump cuts | slam + sonar ping (Marlin's signature), fan spool, roar builds |
| 0:21 | 36 to 56 | **02 ISOLATE** | a cut on every beat: three Marlins vectoring, head-on, top-down, strut, the display closing, the box closes | full power, a whoosh on every cut, passes, hit as the box closes |
| 0:33 | 56 to 60 | (eyes on) | Marlin's thermal view, full frame | the score drops out; hum, two heartbeats, riser |
| 0:35 | 60 to 80 | **03 SURVEIL** | off the foil with a splash, standoff with live feed, partner inbound on the display | slam + splash, heavy and controlled, sonar on each partner update |
| 0:47 | 80 to 96 | Coverage, three words | fleet re-spaces; DETECT. (4 cuts) ISOLATE. (8 cuts) SURVEIL. (held, to black) | a hit on each word, swell into silence |
| 0:56 | 96 | End card | logo, MARLIN, "Detect. Isolate. Surveil." | the biggest hit of the film, rings out. No engine. |

### Narration (46 words)

> A boat is running dark for the coast. / Marlin is already out there. Waiting. Always ready. / It detects the contact. /
> The nearest Marlins vector in. Fifty miles in thirty minutes. / They isolate the contact. / And they stay on it. Until
> partners arrive. / Detect. Isolate. Surveil. / Marlin.

Same content as the approved PDF, re-cut into short sentences for the reference's cadence. "They isolate it" became "They
isolate the contact" because the text-to-speech kept pronouncing it as "isolated". "50 NM · 30 MIN*" and "*Design target"
are on screen while the line is spoken.

### Sound design

- **Score:** original, generated with ElevenLabs Music from a bar-by-bar plan at 104 BPM (`scripts/generate_music_v4.py`);
  six candidates were compared by measurement (tempo, energy curve, a listening model's description) and the darkest,
  most rhythm-driven one was kept. The reference's own track was used for analysis only and is not in the film.
- **Effects:** 14 designed sources (`scripts/generate_sfx_v4.py`) plus synthesized sub booms, heartbeats, pings and air
  swishes, placed on the grid by `scripts/build_audio_v4.py`: impact + sub + braam on every section turn, a whoosh on
  every fast cut, risers and reverse swells into the turns, the sonar ping as Marlin's recurring "detect" sound.
- **Voice:** a licensed stock voice (ElevenLabs "Brian") directed low, gravelly and calm. The reference narrator is a
  named, credited person, so that voice was not cloned.
- **Master:** Spotify Pedalboard (open source). An automation ride gives the film its arc (opening 5 dB under the detect
  slam, finale 1.6 dB over), then glue compression and a limiter. -13.9 LUFS, true peak -1.0 dBFS.
- **Checks:** every source clip, the effects stem and the final mix were scanned with an AudioSet classifier for
  voice-like artifacts (`scripts/audio_qc.py`) and described by a listening model; narration was verified by
  transcription. These are instrument checks, not a human listen.

### New 3D shots (Blender, `blender/previz.py`)

`06b` predator close-up · `v1` three Marlins vectoring in · `i1` isolate, from above · `s1` sensor head sweeps and stops ·
`f1` fan comes alive · `k1` strut slicing the surface · `r2` head-on · `t1` top-down · `10h` the standoff holds.
Clean plates are in `review/v4/reference/`.

## Still needed from Archimedes

- Performance disclaimer wording, demo-request / contact line, vector logo.
- Sign-off on "50 nm in 30 min" as a stated design target.
- Whether "detect" should stay Marlin's own sensor (as drawn) or be shown as a cue from another asset.

## Rebuild

```bash
blender/render_v4.sh && blender/render_v4b.sh          # new plates (CPU, about 50 min)
python3 scripts/generate_music_v4.py 3 1               # score candidates (fal key)
python3 scripts/generate_vo_v4.py                      # narration
python3 scripts/generate_sfx_v4.py                     # effect sources
/opt/venv-audio/bin/python scripts/build_audio_v4.py   # mix + master  (--master-only to re-master the stems)
npx remotion render src/index.ts Marlin review/marlin-animatic-v4.0.mp4 --crf=18
```
