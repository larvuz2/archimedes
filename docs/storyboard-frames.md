# Storyboard sketches: composition reference

Sketches extracted from `reference/Storyboard_V3.pdf` into `reference/frames/shot-NN.png`
(contact sheet: `reference/frames/contact-sheet.png`). Re-extract with `scripts/extract_storyboard_frames.py`.
They're composition guides, not final art. Any change to the narrative needs Archimedes' approval.

## Visual language that runs through all 11 frames
- **Line art on navy.** Thin strokes, no fills. White = hero objects (Marlin, ship, clock). Steel blue-grey = environment and neutral contacts.
- **Color = meaning.** Orange = unknown / threat (NO AIS tracks, go-fast, suspect vessel). Teal = Marlin's foils, sensor cone, tracking rings, links. The **sun is the only other orange**, and it changes between shots 1 and 10.
- **The Marlin silhouette** is the same every time: a long, low wedge hull, a small flat cabin on top, two vertical struts, and **teal T-foils** at the bottom. Keep this read in the 3D model's profile and the HUD icons.
- **Labels** are monospace caps with `·` separators (`MISSION 1 · HARBOR`, `INBOUND · NO AIS`).
- Night shots (7, right half of 8) use a darker navy, ≈ `#0B1520`.

## Per shot

**01 · Port, dawn.** Horizon just above center. Three crane gantries left of center to right (steel), low warehouse blocks on the horizon. White container ship lower-left with containers stacked. Orange sun, **outline only**, top-right. A few short water lines under the ship. *Bookends with 10: lock the camera framing so the two match.*

**02 · Harbor ops console.** `HARBOR OPS` tag top-left over a faint grid. Four steel dots, `AIS 01`–`AIS 04`, sitting still. Orange dashed track enters bottom-left, S-curves to the upper right, arrowhead, `NO AIS`. Second orange dashed arrow pushes in from the right edge, low, labeled `INBOUND · NO AIS` along the bottom. *Animate the dashes drawing on; AIS dots stay frozen to show the contrast.*

**03 · Pier + clock.** Left half: pier deck with two bollards, conventional patrol boat moored underneath, all steel (dim = not moving). Right half: white clock, **orange arc sweeping clockwise** from 12 o'clock along the rim, `TIME TO RESPOND` under it. *Arc grows with the ticking; hard cut to silence on the last frame.*

**04 · Marlin reveal.** Low angle; the waterline is a **rising diagonal** (left low → right high), which gives the climb. Marlin fills the lower two thirds, bow up and to the right, cabin on top, both struts down to teal foils sitting just at/below the water. Steel spray arcs peeling off the stern, bottom-left. Archimedes logo + `MARLIN` stacked top-left, white. *Matches the brief: hull lifts clear, spray drops away, title lands.*

**05 · Speed + reach.** Profile, moving left → right, horizontal speed lines trailing behind. Hull lifted on struts, foils teal. Boxed mono readout `150 KT` top-left (**footnote: design target**). Inset map lower-right: steel coastline, `HARBOR` / `APPROACH` labels, white Marlin dot, inner dashed teal ring and an outer dotted ring that **grows past the inset's edge**, showing reach.

**06 · Mission 1, harbor (bow-camera POV).** Teal corner brackets frame the shot. Horizon line with a crane on the left. Translucent teal **sensor cone** rising from bottom-center. Orange contact boat inside a teal box, labeled `CONTACT 04`, plus `NO AIS` (orange) `→ PORT OPS` (teal). `MISSION 1 · HARBOR` bottom-left. *Generic cone only: no range rings, numbers or sensor names.*

**07 · Mission 2, counter-drug (night).** Darker navy, sparse stars, a **sine-wave sea line** (chop). Marlin on the left, flying above the waves on teal foils; a grey bar extends from it to the right (reads as wake/motion trail or line of sight: **clarify with Archimedes**). Orange go-fast low in the water inside a **teal dashed tracking circle**. Steel `CUTTER` top-right, linked to Marlin by a **teal dotted arc** (the cue / hand-off). Labels: `MISSION 2 · APPROACHES` bottom-left, `SUSPECT VESSEL` orange under the target.

**08 · Split-screen payoff.** Vertical split. Left = day (lighter navy, flat water), Marlin and orange contact. Right = night (darker navy, wavy water), Marlin on foils and orange contact. Bottom strip: `DETECT · CLOSE · IDENTIFY · HAND OFF`, one word per score hit, both sides in sync.

**09 · Network map pull-back.** Top-down. Wavy steel coastlines top and bottom framing the harbor channel. Three teal dashed rings with white arrow icons (Marlins) in a row, a fourth smaller one top-right toward `APPROACHES →`. Dashed lines from each ring converge on a white `PORT OPS` node bottom-center; a dimmer `PARTNERS` node bottom-right. *Generic nodes only, no seals.*

**10 · Port callback.** **Same framing as 01.** Changes that tell the story: the sun is now **filled** (full morning), a crane is **lifting a container** (port working), the ship's container stack has shifted (cargo moving), and a **pier on the right with Marlin moored** small in the lower-right corner.

**11 · End card.** Everything centered: logo, `MARLIN` (bold, wide tracking), `Speed is security.`, a short **orange rule**, `Gregg Scheiferstein, CEO` (bold), email (mono, grey), `[PERFORMANCE / SENSOR DISCLAIMER]` small at the bottom. Hold ≥3s on the contact lines.

## How the sketches shape production
1. **The HUD/graphics shots (2, 3, 5 overlay, 6, 8, 9, 11) can be built very close to these drawings.** They're already in a finished-graphics style; we refine stroke weights, type and motion.
2. **The 3D/live-action shots (1, 4, 5, 7, 10)** follow the sketch's camera angle, framing and screen direction. Line-art overlays from the same system ride on top so the film stays one look.
3. **Option to propose:** open shot 4 (or end shot 10) with a "sketch-to-real" transition, where the line-art Marlin resolves into the rendered craft. It ties the storyboard's look to the product.
4. **Screen direction:** Marlin travels left → right in 5 and is bow-right in 4. In 7 the sketch hull's point is on the left. Decide one direction for the approaches mission and keep it consistent.
