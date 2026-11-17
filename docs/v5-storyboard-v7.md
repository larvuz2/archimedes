# Animatic v5.0: Storyboard V7 and the narration note

**Inputs** (17 Nov):

- **Storyboard V7:** *Marlin: Intercept. Surveil. Stop.* Delivered as `Marlin_Counter-Drug_Storyboard_v6.pdf` and saved in `docs/reference/`. It has 14 shots, a 27-word script, clearance notes and a page of fixes against the v4.0 demo.
- **Note on v4.0:** "my only note is the VO is too flat - needs more emotion / urgency / intensity / that's it!"

**Review file:** `review/marlin-animatic-v5.0.mp4` (60 s, 1080p, 24 fps).

## The page-6 fixes

| # | Issue in the v4.0 demo | Fix in v5.0 |
|---|---|---|
| 01 | Slow start, no gap: about 7 s of Marlin "ON STATION" before anything happens | Opens on the boat (01), the designated target on the aircraft radar (02) and the gap, where no asset can reach it (03). Marlins first appear in 04, when they are tasked. |
| 02 | Marlin detects ("SENSOR · SEARCHING", "01 DETECT") | Cut. The aircraft radar shows the intel cue, the hook and "CUE ✓ · DETECTED ✓ · DESIGNATED ✓". Marlin is tasked by C2 ("C2 · TASK MARLIN ×2", "TASKED"). Marlin never searches, detects or designates. |
| 03 | "Isolate": three Marlins box the target | Two Marlins: one head-on up the track, one on the flank (06, labelled on the display). No "isolate" anywhere. |
| 04 | No stop | Act 3 added as one notional, operator-selected profile: authorization (08), pass (09), net away (10), props fouled and dead in the water (11), hold (12). Five new 3D shots. |
| 05 | Caption "FLEET RE-SPACES · COVERAGE HOLDS" | Dropped. The arrows and rings carry it (13). |
| 06 | Seven seconds of full-screen "DETECT. ISOLATE. SURVEIL." | The tagline lands over the fleet map (13), one word per hit, then a 4 s end card. |
| 07 | Triad "Detect · Isolate · Surveil" | Supers "01 INTERCEPT · 02 SURVEIL · 03 STOP". End card "Intercept. Surveil. Stop." [pause] "Marlin." |

## The narration: more emotion, urgency, intensity

The v4 read was directed "low, gravelly, calm". For v5 the narration was auditioned rather than assumed.

1. **Auditions.** 16 takes of the same two lines: five ElevenLabs voices (Brian, Callum, Bill, Roger, Daniel) in three directions, plus four MiniMax voices. The scripts are `scripts/vo_audition_v5.py` and `vo_rate_v5.py`.
2. **Scoring.**
   - **1–10 scores dropped.** The listening model gave the v4 read the client called flat 8.5, the same as most new takes, so its absolute scores were not used.
   - **Head-to-head instead.** Each take was played against the v4 read in both orders, because the model favours whichever take plays second (`scripts/vo_ab_v5.py`).
   - **The winner.** Only Callum, directed "epic movie trailer narrator, deep and intense, rising urgency" at the most expressive setting, won in both orders.
3. **Recording.** Four to six takes of every line (`scripts/generate_vo_v5.py`). Takes were rejected for wrong words (Whisper), glitches or shouting (listening check). Of the rest, the take with the most vocal energy for that line was kept: vocal effort, pitch lift and movement, loudness contrast (`scripts/pick_vo_v5.py`).
4. **Result.** The finished narration, against the v4 narration, head-to-head in both orders: the new read wins both ways, margin 8/10, described as "urgent, intense, dramatic, gravelly, powerful".

The narrator's voice has changed (Brian → Callum). A different voice was the clearest way to more intensity.

**Script (27 words, as V7):** "Tasked, the nearest two close fifty miles in thirty minutes, put eyes on, and stop it dead in the water until partners arrive. Intercept. Surveil. Stop. Marlin."

## The cut

The new score runs at exactly 104 BPM with its first beat at 0.055 s. Every shot starts on a beat, within 0.35 s of the storyboard's timecode.

| Shot | V7 time | v5 time | Picture | Narration | Sound |
|---|---|---|---|---|---|
| 01 The boat | 0:00 | 0:00.06 | go-fast, tight, moving (punch-in on the crew) | | pulse from frame one, outboards flat out |
| 02 Detected and designated | 0:04 | 0:04.09 | aircraft radar: intel cue, hook, CUE ✓ DETECTED ✓ DESIGNATED ✓, TOI-01 · SUSPECT GO-FAST | | sweep tones, muffled aircraft drone, the score tightens |
| 03 No end game | 0:09 | 0:09.29 | pull back to the COP; aircraft breaks off; cutter far, USV slow; track goes dashed | | the score sinks (tape-stop) to silence |
| 04 Tasked | 0:14 | 0:13.90 | twenty Marlins on station, rings tile; C2 · TASK MARLIN ×2; TASKED; intercept lines | | one held tone in the silence, a low swell into the kick |
| 05 Lift | 0:18 | 0:18.52 | fan spools, climbs onto the foils, gone; **01 INTERCEPT** | "Tasked, the nearest two close" | the kick, fan to full roar |
| 06 Converge | 0:22 | 0:21.98 | head-on and flank closing; 50 NM · 30 MIN* (design target) | "fifty miles in thirty minutes," | a data tone on each track update |
| 07 Eyes on | 0:26 | 0:26.02 | MARLIN IR, 3 POB · BALES, LIVE TO C2; pull out to the standoff; **02 SURVEIL** | "put eyes on," | fan drops to a hull-borne hum, hull slap |
| 08 Authorized | 0:31 | 0:31.21 | course-up display: C2 · STOP AUTHORIZED · PROFILE: V-NET, NOTIONAL STOP PROFILE; the pass path and the V draw themselves | | one confirm tone, the score builds |
| 09 Pass | 0:34 | 0:34.67 | overhead: the lead lifts, passes wide, cuts in ahead; **03 STOP** | "and stop it dead in the water" | slam; fan roar passes, the outboards answer |
| 10 Net away | 0:38 | 0:38.13 | overhead: the net leaves the stern, two legs land in a V; dashed turn arrows; NET AWAY | | pneumatic thump, the net slaps the water |
| 11 Fouled | 0:42 | 0:41.59 | the go-fast swerves into a leg; underwater inset PROP FOULED; TOI-01 · DIW | | outboards choke and die, the score stops with them, then only water |
| 12 Hold | 0:46 | 0:46.21 | dead in the water; both Marlins at standoff, eyes on; partner closing; PARTNER EN ROUTE, DIW | "until partners arrive." | idle hum, a distant engine growing |
| 13 The fleet | 0:50 | 0:50.82 | pull back to the full picture (framed like 03); five Marlins slide over, rings re-tile; words land one per hit | "Intercept. Surveil. Stop." | the score resolves, three hits |
| 14 End card | 0:56 | 0:56.02 | hard cut to navy, a beat of silence, logo, MARLIN, tagline, contact, disclaimer | [pause] "Marlin." | single fan spool-up to black |

## Sound checks

Sound was checked by instruments, not by ear.

- **Rejected effect.** The generated "swerve" effect had a scream in it, so it was deleted. The swerve uses the go-fast clip that was already checked.
- **Generated net slap.** In the mix it read as a "gobble", so it was replaced by synthesized splashes.
- **The riser before the lift.** It sat exposed in near-silence, and the listening check said it could pass for an electronic scream. It was replaced by a low swell.
- **Final mix.**
  - The voice-artifact classifier is clean: worst reading 0.02.
  - The listening model hears no voice other than the narrator, and no glitches.
  - Every narration line was heard and transcribed.
  - Loudness is -14.0 LUFS, true peak -2.1 dBFS.

## Clearance notes applied

- **Detection and designation.** Shown as the enterprise's work (aircraft radar, intel cue box). Marlin never searches, detects or designates.
- **Use of force.**
  - "C2 · STOP AUTHORIZED" is on screen before the stop.
  - No weapons, no "target acquired", no "lock" or "engage".
  - The stop is the net fouling the props.
- **Stop profile.** "NOTIONAL STOP PROFILE" is captioned in 08, 09 and 10. C2 selects the profile ("PROFILE: V-NET"); Marlin executes it.
- **Net naming.** "V-NET" and "NET AWAY" only. The trademarked system name is not used.
- **Performance claims.**
  - "50 NM · 30 MIN*" carries "*Design target".
  - The disclaimer covers 50 nm in 30 min, hull-borne shadowing and the stop.
- **Marks and geography.**
  - Asset types only. The partner boat is plain grey with standard navigation lights and no markings.
  - Stylized coastline. Marlin in defense grey.

## Decisions to confirm

1. **The end card sound.** V7 asks for a "single fan spool-up to black". On 13 Nov the client said they did not like the buzz at the end. v5 uses a short, low, soft spool-up under the fade; it is easy to remove.
2. **Narrator voice change** (Brian → Callum), as above.
3. **The new 3D shots are blockout previz.**
   - The net is a floated head rope with floats.
   - The launcher is two notional tubes on the after body.
   - The underwater cutaway is slowed down for readability.
4. **Still needed from Archimedes:** disclaimer wording, the demo-request / contact line, the vector logo, and sign-off on the notional stop profile.

## Rebuild

```bash
blender/render_v5.sh                                   # new 3D shots p1 n1 x1 h1 u1 (CPU, about 70 min)
python3 scripts/generate_music_v5.py 4                 # score candidates (candidate 2 is public/audio/v5/music.mp3)
python3 scripts/generate_vo_v5.py 4                    # narration takes
/opt/venv-audio/bin/python scripts/pick_vo_v5.py       # keep the best take of each line
python3 scripts/generate_sfx_v5.py                     # new effect sources
/opt/venv-audio/bin/python scripts/build_audio_v5.py   # mix + master
npx remotion render src/index.ts Marlin review/marlin-animatic-v5.0.mp4 --crf=17
```
