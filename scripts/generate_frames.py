"""Generate cinematic storyboard frames with GPT Image 2.5 (fal.ai, openai/gpt-image-2.5/flare/edit).

Every frame = the SAME cinematography block + the SAME product description + that shot's
composition. The Marlin reference sheet is attached to every generation.
Writes public/frames/<id>.jpg and docs/frames/prompts/<id>.txt (the exact prompt used).

  python3 scripts/generate_frames.py            # all frames
  python3 scripts/generate_frames.py --only f06 f07
"""
import argparse, base64, json, os, pathlib, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = ROOT / 'public/assets/models/marlin-reference-sheet.jpg'
OUT = ROOT / 'public/frames'
PROMPTS = ROOT / 'docs/frames/prompts'
ENDPOINT = 'https://fal.run/openai/gpt-image-2.5/flare/edit'

CINEMATOGRAPHY = """CINEMATOGRAPHY — apply identically to every frame of this film:
Photoreal cinematic film still from a premium defense-technology commercial. Shot on ARRI Alexa 65 with Panavision Ultra Vista anamorphic lenses, 16:9 frame. Naturalistic, motivated lighting only (sun, moon, practical lamps, screens, beacons); deep rich shadows with detail, controlled highlights, high dynamic range, no crushed blacks, no clipped skies. Color grade: cool teal and steel-blue in the shadows and water, warm amber in sunlight and practical lights, restrained saturation, filmic contrast curve. Subtle horizontal anamorphic flares only from real light sources, oval bokeh, gentle vignette, fine 35mm film grain. Atmospheric sea haze and mist for depth. Physically accurate ocean: correct wave scale, foam, spray, wakes and reflections. Composition on the rule of thirds with strong leading lines and clear foreground, midground and background separation. Restrained, credible, documentary-grade realism in the style of a Roger Deakins or Claudio Miranda maritime sequence; confident, not aggressive. STRICTLY: no text, no captions, no letters or numbers anywhere, no logos, no watermarks, no flags, no agency seals, insignia or hull markings, no weapons, no identifiable faces."""

PRODUCT = """THE PRODUCT — MARLIN (the attached reference sheet is the single source of truth; match its design, proportions, parts and colors exactly, do not add or remove features):
An uncrewed, autonomous hydrofoil drone. No cabin, no cockpit, no windows, no people aboard. A long, smooth, rounded torpedo-like pod hull in glossy white with a navy-blue band along its side and a dark charcoal underside, fine panel lines and small access hatches on top. At the stern stands a large circular ducted fan: a white duct ring with a navy-blue rim, housing a three-blade dark-grey propeller with a white spinner, the ring rising well above the hull. Behind the duct, a navy-blue V-shaped tail fin on a white vertical pylon. On top of the duct ring, a short grey sensor mast with a horizontal sensor bar and a thin antenna, flanked by two blue beacon lights. A single dark raked hydrofoil strut extends down from beneath the forward hull into the water. When foiling, the hull rides clear above the surface on that strut, with a clean thin plume of spray where the strut cuts the water. It is compact (under 24 feet long)."""

NO_MARLIN = "Marlin does NOT appear in this frame; the reference sheet is attached only for continuity of the film."

FRAMES = {
    'f01': ("Night sea, the gap", NO_MARLIN + """
Extreme wide establishing shot at night over the open ocean under a moonless sky with faint stars. Far away on the horizon, a thin line of coastal city lights glows warm amber. In the lower-left third, a small, low, unlit fast open boat with outboard engines cuts diagonally across the black water toward the coast, leaving a long pale wake that is the brightest element in frame; the boat itself is nearly a silhouette, its occupants indistinct shapes. Camera: high drone perspective about 40 meters up, 24mm, tilted down, slow push. Lighting: cold blue moonless ambient, faint starlight on the swell. Mood: quiet, ominous, something slipping through."""),
    'f02': ("Operations center", NO_MARLIN + """
Medium shot inside a dim, modern maritime operations center at night. In the soft-focus foreground, the shoulder and back of a seated operator in a dark sweater (face not visible). They look at a large wall display showing a dark abstract nautical chart: a coastline, a few small grey vessel dots sitting still, and one bright orange dotted track line curving fast toward the coast. Screens use abstract symbols only, no readable text or numbers. The display is the main light source, casting cool blue and orange glow across the room; a second row of dark monitors falls off into shadow. Camera: 50mm anamorphic at seated eye level, shallow focus on the orange track. Mood: realization, urgency."""),
    'f03': ("Patrol at the pier", NO_MARLIN + """
Blue hour before dawn at a working harbor pier. A generic conventional patrol boat (grey rigid-hull inflatable with a center console and twin outboards, no markings, no lettering) is still tied to the dock. Two crew members in generic dark-navy foul-weather jackets and life vests hurry down the pier toward it carrying gear, seen from behind at medium-wide distance, faces not visible. Warm sodium-vapor dock lights make amber pools on wet planks against a cold blue sky. Camera: low angle at dock level, 35mm; a mooring line and cleat soft in the foreground. Mood: effort and delay, the response has not left yet."""),
    'f04': ("Patrol in heavy chop", NO_MARLIN + """
The same generic grey patrol boat as in the second attached image (grey rigid-hull inflatable with a center console and twin outboards, no markings), now underway with its two crew aboard, pounding through steep, heavy chop in open water, its bow slamming into a wave and throwing a wall of white spray, the hull pitching hard, visibly slowed. Overcast dawn, steel-grey sea with wind streaks and whitecaps, rain haze. The crew are small, hunched, indistinct. Camera: 200mm telephoto from a chase position ahead and to the side, compressing the waves into a wall; slight handheld energy. Mood: struggle, time lost."""),
    'f05': ("Marlin wakes", """
Night at a quiet, modern floating dock. Marlin rests in the water, hull floating with its strut submerged, moored alongside the dock. Its two blue beacon lights have just switched on, throwing blue light across the white duct ring and rippling over the black water; a faint glow on the sensor mast. Camera: low angle near the waterline, 40mm anamorphic, front three-quarter view of Marlin filling the right two-thirds of the frame; warm dock lights bokeh in the background, thin mist on the water. Mood: a machine waking up, calm before the launch, anticipation."""),
    'f06': ("Marlin rises — title", """
Dawn breaking, golden sun just above the horizon. Marlin accelerates away from camera and lifts onto its hydrofoil: the hull rising clear of the water on its single strut, ducted fan spinning with motion-blurred blades, a dramatic sheet of spray and mist backlit and glowing gold by the low sun. Camera: right at the waterline, low and close, 32mm, rear three-quarter view as it pulls away; a few droplets catching light near the lens. Upper third of frame stays clean sky for a title. Mood: the hero reveal, awe and optimism."""),
    'f07': ("01 Get there", """
Full-speed tracking shot: Marlin foiling flat and level at very high speed across the open ocean, hull fully clear of the water, only the strut slicing the surface and throwing a thin knife-edge rooster tail of spray; fan blades motion-blurred. Bright morning light, deep-blue sea with moderate chop and whitecaps. Camera: helicopter tracking alongside at matched speed, side profile with Marlin travelling left to right (nose pointing to frame right), 85mm, water streaked with panning motion blur while Marlin stays tack sharp. Marlin on the left third with generous lead room ahead. Mood: pure speed and stability."""),
    'f08': ("02 See it", """
Over-the-shoulder shot from just behind and above Marlin's sensor mast: the mast, sensor bar and the two blue beacons are large and soft-focus in the left foreground. Across the water, about 300 meters away in the right third of frame and in sharp focus, a small dark fast open boat with outboard engines (occupants indistinct). Late afternoon, low sun, light haze, glittering sea. Marlin is holding at a standoff on its foil, watching. Camera: 100mm telephoto compression, shallow depth of field. Clean negative space around the distant boat for a graphic overlay. Mood: calm, observational, in control."""),
    'f09': ("03 Stay on it", """
Dusk turning to night on rough open water. The small dark fast open boat (unlit, outboards, occupants indistinct) runs away in the midground right, throwing spray. Close behind it, Marlin follows on its foil in the left foreground, sharp, both blue beacon lights flashing brightly and washing the spray, the waves and the mist in vivid blue light. Camera: low, 35mm, chase position behind and to the side of Marlin. Mood: tense but controlled; it is not letting go."""),
    'f10': ("Partner cutter closing", NO_MARLIN.replace('does NOT appear in this frame', 'appears only as two tiny distant flashing blue lights') + """
Night at sea. A generic white patrol cutter (medium size, clean white hull, grey superstructure, no stripes, no lettering, no numbers, no flags, no insignia) drives in fast from the right, bow throwing spray, a searchlight beam cutting through sea mist. Far in the left background, a tiny pair of flashing blue lights marks Marlin holding on the target. Camera: wide 28mm from near the waterline at the cutter's bow quarter. Mood: the hand-off, help arriving."""),
    'f11': ("Recap — mission complete", """
First light at dawn on a calm sea. In the soft-focus background, the same white patrol cutter as in the second attached image (clean white hull, grey superstructure, no stripes, no markings; a civilian patrol cutter, not a grey warship) lies alongside the small dark open boat; a small, indistinct boarding team works calmly, no force shown. In the right foreground, Marlin rests settled on the water, hull floating, beacons off, its white hull catching the warm sunrise, watching from a respectful distance. Camera: 50mm, low near the water, Marlin sharp in the foreground. Mood: resolution, quiet confidence, mission accomplished."""),
    'f12': ("Hero beauty shot", """
Iconic beauty shot at golden hour: Marlin foiling at speed across glassy water, travelling toward frame left, the low sun behind it rimming the hull, duct ring and tail fin with gold light, spray glowing. Composition: Marlin small in the lower-right third; vast negative space of warm sky and sea in the center and upper frame for a logo and title. Camera: 135mm from slightly ahead and to the side. Mood: premium, inevitable, the future of maritime response."""),
}


def prompt_for(fid):
    title, comp = FRAMES[fid]
    return f"{CINEMATOGRAPHY}\n\n{PRODUCT}\n\nSHOT {fid.upper()} — {title.upper()}. COMPOSITION, CAMERA AND LIGHTING FOR THIS FRAME:\n{comp.strip()}"


# Extra continuity references: earlier frames attached after the reference sheet.
CONTINUITY = {'f04': ['f03'], 'f11': ['f10']}


def data_uri(path):
    return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode()


def gen(fid):
    refs = [data_uri(REF)] + [data_uri(OUT / f'{c}.jpg') for c in CONTINUITY.get(fid, [])]
    body = dict(prompt=prompt_for(fid), image_urls=refs, image_size={'width': 1920, 'height': 1080},
                quality='high', output_format='jpeg', num_images=1)
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={
        'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=600))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{fid}.jpg').write_bytes(urllib.request.urlopen(res['images'][0]['url'], timeout=300).read())
    return fid


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    ids = a.only or list(FRAMES)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    for fid in ids:
        (PROMPTS / f'{fid}.txt').write_text(prompt_for(fid))
    with ThreadPoolExecutor(6) as ex:
        for fid in ex.map(gen, ids):
            print('wrote', fid)
