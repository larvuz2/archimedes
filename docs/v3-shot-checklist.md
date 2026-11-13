# Animatic v3.0: checked against Storyboard V5, line by line

Source of truth: `docs/reference/Marlin_Counter-Drug_Storyboard_v2.pdf` (titled "Storyboard V5" inside; the re-upload on
13 Nov is byte-identical to the file v2.0 was built from). Render: `review/marlin-animatic-v3.0.mp4`, 24 fps.

**How it is made now**
- **3D shots (01, 03, 06, 07, 09, 10): Blender blockout previz**, built entirely from `blender/previz.py`
  (models, night ocean, moonlight, spray, animated vessels and camera). Scenes: `blender/scenes/*.blend`.
  Clean plates for the video model: `review/v3/reference/`.
- **2D shots (02, 04, 05, 08, 11, 12): code-built displays** in `src/v3/` (radar, common operational picture, end card).
- **Sound: every effect is synthesized** in `scripts/build_audio_v3.py` (nothing generated, so nothing can contain a
  voice) and every stem is scanned with an AudioSet classifier (`scripts/audio_qc.py`).

## Shot by shot

| Shot | Storyboard says | In v3.0 |
|---|---|---|
| **01 · The boat** 0:00–0:04 | Night, open sea. A low go-fast runs flat out with no lights, spray sheeting off the bow, bales lashed down, men hunched behind the console. Tight and moving with it. No VO, nothing on screen. Hard pulse score from frame one; outboards. | Blender. Low open hull, no T-top, no lights, twin outboards. Bales in two layers under straps. Three figures hunched behind a low console. Spray sheets off both bows + rooster tail. Camera tracks tight with the boat at 30 kt, sliding from the bow quarter to the men. Moonlit open ocean, no coastline. Score from frame one, synthesized outboards. |
| **02 · Aircraft radar** 0:04–0:07 | Sea-search radar. Sweep paints clutter inside a dashed search box. One faint return holds sweep after sweep; operator hooks it. AOI box, hook brackets, "CONTACT". Radar sweep tone; muffled aircraft drone. | Sector scan crosses the contact four times (0:04.35, 05.10, 05.85, 06.60); clutter speckle changes every sweep, the return does not. Hooked at 0:06.05 with brackets + CONTACT. Sweep tone, return blips, turboprop drone. |
| **03 · Infrared ID** 0:07–0:10 | Aircraft IR camera slews onto the contact: white-hot go-fast, twin wakes, bales on deck. Tag "TOI-01 · GO-FAST / NO NAV LTS · 3 POB". Servo whir; outboards under the score. | Blender thermal pass from 900 m slant range, 38° down (matches "EL -38"). Camera slews on with a small overshoot; brackets and tag land when it settles. IR WHT / NFOV / AZ 214 EL -38. Servo whine, outboards low under the score. |
| **04 · Out of reach** 0:10–0:16 | Pull back to the COP: stylized coastline, open water, scale bar. Aircraft orbits. Cutter far offshore, USV close but slow; neither reach ring comes near. Aircraft breaks off; track turns dashed, projected to the coast. Tag adds "· 30 KT". Console tones; score drops to silence as the track goes dashed. | Pull-back from the contact. MPA on a dashed orbit, breaks off at 0:12.8. CUTTER and USV · 3 KT with 30-minute rings. Track goes dashed with an arrowhead at the coast from 0:13.4; score is silent by 0:14.3. |
| **05 · On station** 0:16–0:20 | Same display, no cut. Twenty Marlin markers blink on, each with a tight looping trail. 30-minute rings tile the approaches. Projected track runs straight at one Marlin; a second off its flank. Markers and rings only. One held tone in the silence, then the score starts to rebuild. | Same component, no cut. 20 markers with looping station-keeping trails, rings tile, the nearest two highlight with a MARLIN label. TOI text hidden (markers and rings only). Held tone at 0:16, score returns from 0:17.5. |
| **06 · Loiter** 0:20–0:23 | Open ocean, night, long swell. A defense-gray Marlin sits hull-borne, alone, sensor mast turning. Water and wind; pulse returns underneath. | Blender. Gray Marlin (from the reference sheet, no lights) riding the swell, sensor bar rotating, moon and glitter path, slow push. Water lapping + light wind. |
| **07 · Lift** 0:23–0:28 | Camera at the waterline. Marlin spools up, climbs onto its foils and the spray falls away. Out of frame in seconds. VO "The nearest two close fifty miles in thirty minutes,". Super "01 CLOSE". Engine spools to a full roar; score kicks in on the lift. | Blender. Camera 0.3 m above the surface. Fan wash, hull ploughs, lifts at about 0:24.3–0:25.5, passes camera and is out of frame by about 0:26.4; spray settles. VO at 0:23.3, super from 0:23.0, *Design target footnote. Score kick at 0:24.0. |
| **08 · Converge** 0:28–0:34 | Display, tight. Marlin ahead runs straight up the projected track; second angles in from the flank to a point beside the track. Readout "50 NM · 30 MIN". Data tone on each track update. | Tight COP. HEAD-ON and FLANK tracks with arrows, intercept point on the track, aim point beside it. Four stepped track updates, each with a data tone. Readout with *Design target. |
| **09 · The run** 0:34–0:40 | Drone tracking shot alongside a Marlin flying level over night chop, hull clear of the water and steady as the sea builds. Full engine roar, wind buffeting the mic. | Blender. 100 kt, hull clear on the strut, rock steady while the wave height doubles over the shot. Drone slides from the bow quarter to the beam. Fan roar + wind buffet. |
| **10 · Eyes on** 0:40–0:46 | Marlin's own IR view of the go-fast (same look as 03). Pull out: Marlin comes about, drops off its foils, settles hull-borne at standoff, pacing the boat; second Marlin on its flank. VO "and stay on it until partners arrive." Supers "02 EYES ON", "03 SURVEIL". Inset "● LIVE". Tag "PARTNER EN ROUTE". Engine drops to a rumble; hull slap; distant radio. | Blender thermal pass full frame 0:40–0:41.5, then it shrinks into the LIVE inset (top right) over the wide shot: Marlin turns onto the boat's course, comes down off the foil with a splash, paces hull-borne; second Marlin beyond. Line of sight mast → go-fast. Supers at 0:40 and 0:42. Radio is squelch/static only, no voice. |
| **11 · The fleet** 0:46–0:56 | Pull back to the full display, framed exactly like shot 04. Two Marlins hold the boat. Five nearby slide over, rings re-tile with no holes. Short arrows on the five. Three words one per beat. Score broadens and resolves; three hits. | Same framing as 04. Two hold the contact, five slide over with arrows, rings re-tile. PARTNER track inbound. COVER. / SPRINT. / PERSIST. land on the VO words with three hits. |
| **12 · End card** 0:56–1:00 | Hard cut to navy. A beat of silence, then logo and product name land. VO [pause] "Marlin." Logo · MARLIN · Cover. Sprint. Persist. · [DEMO REQUEST / CONTACT] · disclaimer. Single engine rev to black. | Hard cut, 0.75 s of silence, logo + MARLIN land, "Marlin." at 0:57.1, tagline, contact placeholder, disclaimer, one fan rev, fade to black. |

## The 13 fixes on page 6
All still applied (see `docs/v2-client-fixes.md`); v3.0 strengthens 01, 04, 05, 08 and 10 by showing real motion in 3D:
no coastline or lights in the opening, Marlin loitering at sea (not at a pier), defense gray with no light bar,
hull-borne while shadowing and foil-borne only in transit, one continuous night.

## Clearance items from page 1 (unchanged, still need Archimedes)
- "50 nm in 30 minutes" and hull-borne shadowing carry a *Design target* caption until test data exists.
- Asset types only (MPA, CUTTER, USV, PARTNER); no seals, hull numbers or agency colors. Marlin in defense gray.
- Generic radar and infrared depictions; the cue appears only as a search box.
- Stylized coastline only. No "target acquired", "lock" or "engage" language.
- End card placeholders: `[DEMO REQUEST · CONTACT]`, `[PERFORMANCE DISCLAIMER]`, logo vector.
