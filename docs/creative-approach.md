# Creative approach (draft, for Phatty Acid review)

## The idea: "From the console to the water"
The storyboard already has a strong visual language: navy fields, thin white line work, **orange for
unknown contacts**, **teal for Marlin**. We keep that language as the spine of the film. It starts as
the port-ops screen in Act 1, comes off the screen and wraps around the real craft in Act 2 (HUD
overlays riding on the water), and pulls back into the networked map in Act 3. One visual system
from first frame to end card is what makes it feel engineered, not hyped.

Tone: measured, confident, credible. Think a well-made engineering film, not a trailer. No slow-mo
explosions, no aggressive tactics, no agency marks.

## Shot types → tools

| Type | Shots | Tool | Why |
|---|---|---|---|
| Port establishing (live action) | 1, 10 | Licensed stock aerial (port clearance if identifiable) | Brief and storyboard ask for real b-roll; real footage buys credibility. |
| Pier / conventional patrol | 3 | Stock, generic unmarked boat + clock graphic | No agency uniforms or markings. |
| Marlin hero (3D) | 4, 5, 7, (10 at pier) | 3D from the client's model. Stylized: three.js in Remotion. Photoreal: Blender/Unreal on a GPU box | Marlin doesn't exist yet as footage, so it has to be CG. Hero water/spray is where the money shows. |
| HUD / console / overlays | 2, 6, 7 overlay, 8 | Remotion (SVG + React) | Precise, on-brand, easy revisions, frame-accurate sync to VO and score hits. |
| Map / network | 5 inset, 9 | Remotion (SVG paths, animated rings) | Generic nodes only, no seals. |
| Titles, specs, end card | 4, 5, 11 | Remotion | Disclaimers and "design target" footnotes stay legible and controlled. |

**Gen-AI video (Veo/Runway/etc.):** I'd keep it off the hero craft. It invents details (hull shape,
markings, flags) and a government audience will notice. At most, use it for atmosphere plates
(sky, water texture), and only if Archimedes is OK with that.

## Pacing (60s, 11 shots, timings from Storyboard V3)
- **Act 1 (0–14s):** calm → unease. Slow push, cold console, ticking clock, hard cut to silence.
- **Act 2 (14–45s):** the silence breaks with the engine. Fastest cutting is shot 5. Missions 1 and 2
  use the same playbook so the audience learns it twice; shot 8 lands it on four score hits.
- **Act 3 (45–60s):** scale up to the system, come back to the calm port, end card holds ≥3s on contact info.

## Sound
- **VO:** 137 words. Fits 60s at a calm pace (~145 max per storyboard). Calm, authoritative read.
  Scratch VO with a TTS voice for timing, then real talent for final.
- **Music:** low synth pulse, builds through Act 2, four hits on Detect/Close/Identify/Hand off,
  resolves in Act 3. Licensed library track cut to picture, or a custom cue.
- **SFX:** real engine and water recordings (storyboard asks for this); soft UI tones for the HUD.

## Deliverables to propose
- 16:9 1920×1080 master (4K if the 3D pipeline allows), 30fps.
- Captioned version + SRT (much of this audience watches muted on LinkedIn / in briefings).
- Optional cutdowns: 30s and 1:1 / 9:16 social. Remotion makes re-formatting cheap.
