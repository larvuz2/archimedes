"""Generate cinematic storyboard frames with GPT Image 2.5 (fal.ai, openai/gpt-image-2.5/flare/edit).

Every frame = the SAME cinematography block + the SAME product description + that shot's
composition. The Marlin reference sheet is attached to every generation.
Storyboard V5 (client v2): one continuous night, defense-gray Marlin.
Writes public/frames/v2/<id>.jpg and docs/frames/v2/prompts/<id>.txt (the exact prompt used).
Frames listed in CONTINUITY need their reference frames generated first.

  python3 scripts/generate_frames.py            # all frames
  python3 scripts/generate_frames.py --only a06 a07
"""
import argparse, base64, json, os, pathlib, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Storyboard V5: defense-gray Marlin (made by scripts/make_gray_reference.py from the client sheet)
REF = ROOT / 'public/assets/models/marlin-reference-sheet-gray.jpg'
OUT = ROOT / 'public/frames/v2'
PROMPTS = ROOT / 'docs/frames/v2/prompts'
ENDPOINT = 'https://fal.run/openai/gpt-image-2.5/flare/edit'

CINEMATOGRAPHY = """CINEMATOGRAPHY — apply identically to every frame of this film:
Photoreal cinematic film still from a premium maritime-technology commercial. Shot on ARRI Alexa 65 with Panavision Ultra Vista anamorphic lenses, 16:9 frame. ONE CONTINUOUS NIGHT: every frame is the same moonlit night on the open ocean. Cool silver-blue moonlight from a high half moon, deep navy sky with faint stars, moon glitter on the swell. No sunset, no dawn, no daylight, no coastline, no city lights. Low-key, naturalistic, motivated lighting only (moon, starlight, sea reflections); rich deep shadows that still hold detail, controlled highlights, no crushed blacks. Color grade: steel-blue and teal shadows, silver highlights, restrained saturation, filmic contrast curve. Subtle horizontal anamorphic flares only from real light sources, oval bokeh, gentle vignette, fine 35mm film grain. Light sea mist for depth. Physically accurate ocean: correct wave scale, foam, spray and wakes. Rule-of-thirds composition with clear foreground, midground and background. Credible, documentary-grade realism in the style of a Roger Deakins night-at-sea sequence; serious, confident, not aggressive. STRICTLY: no text, no captions, no letters or numbers, no logos, no watermarks, no flags, no seals, insignia or hull markings, no weapons, no identifiable faces."""

PRODUCT = """THE PRODUCT — MARLIN (the attached gray reference sheet is the single source of truth; match its design, proportions, parts and colors exactly, do not add or remove features):
An uncrewed, autonomous hydrofoil vessel. No cabin, no cockpit, no windows, no people aboard. Painted entirely in a uniform matte cool slate gray with a slightly darker gray band and a dark charcoal underside; no white, no blue. NO lights of any kind on it: no beacons, no light bar, no strobes. A long, smooth, rounded pod hull with fine panel lines and small hatches on top. At the stern stands a large circular ducted fan: a gray duct ring housing a three-blade dark propeller with a gray spinner, rising well above the hull. Behind the duct, a gray V-shaped tail fin on a vertical pylon. On top of the duct ring, a short sensor mast with a horizontal sensor bar and a thin antenna. A single dark raked hydrofoil strut extends down from beneath the forward hull. Hull-borne: it floats low on its hull with the strut in the water. Foil-borne: the hull rides clear above the surface on the strut, with a thin plume of spray where the strut cuts the water. Compact, under 24 feet long."""

NO_MARLIN = "Marlin does NOT appear in this frame; the reference sheet is attached only for continuity of the film."

BOAT = ("a long, low, open fiberglass speedboat with twin large outboard engines, running with no lights, "
        "wrapped cargo bundles strapped down on its deck, three crew hunched low behind a center console (faces not visible)")

FRAMES = {
    'a01': ("The boat", NO_MARLIN + f"""
Tight, fast, moving shot of {BOAT}, running flat out across the open ocean at night. Spray sheets off the bow and glows silver in the moonlight; the outboards throw a white rooster tail. Camera: 35mm from a chase position just off the bow quarter at water level, moving with the boat, slight motion blur on the water, the boat filling most of the frame. Mood: urgent, fast, dangerous."""),
    'a03': ("Infrared ID from the aircraft", NO_MARLIN + f"""
Thermal infrared camera image as seen by a patrol aircraft at night: monochrome white-hot rendering (hot is white, cold is black), black-and-gray tones, slight sensor noise and soft vignetting. Looking steeply down from altitude at {BOAT}: the hull and engines glow white-hot, twin wakes trail behind as two bright streaks, the cargo bundles read as lighter blocks on deck, the crew as small warm shapes. The boat sits diagonally across the center of frame, surrounded by dark textured sea. No overlay graphics, crosshairs or text (graphics are added later). Same boat as the second attached image."""),
    'a06': ("Loiter", """
Open ocean at night under moonlight, long slow swell. Marlin sits hull-borne, floating low on the water with its strut submerged, completely alone in a vast empty sea, the sensor mast on top of the duct. It has been out here for days: faint salt streaks on the gray paint. Camera: wide, 50mm, low near the water; Marlin medium-small in the right third; a moon glitter path on the water leads the eye to it; huge negative space of sea and starry sky. Mood: patient, persistent, quietly waiting."""),
    'a07': ("Lift", """
Camera right at the waterline, low and close, 28mm, front three-quarter view. Marlin spools up and climbs onto its single hydrofoil strut: the hull rising clear of the water, the ducted fan blades motion-blurred, a sheet of spray falling away and backlit by the moon into silver mist. Strong sense of acceleration, Marlin about to leave frame left. Same night, same sea as the second attached image."""),
    'a09': ("The run", """
Drone tracking shot alongside Marlin flying level at very high speed over dark night chop, hull fully clear of the water on its strut, perfectly steady as the sea builds beneath it; a thin knife-edge plume of spray from the strut glows silver in the moonlight; fan blades motion-blurred. Side profile travelling left to right (nose pointing to frame right), 85mm, water streaked with motion blur while Marlin stays tack sharp, generous lead room ahead. Same night as the second attached image. Mood: speed you can feel."""),
    'a10a': ("Eyes on — Marlin infrared view", NO_MARLIN + f"""
A TRUE THERMAL INFRARED camera image, fully monochrome grayscale with zero color: white-hot rendering (hot is white, cold is black), like real FLIR footage, slight sensor noise, soft vignetting. Thermal cameras do not see moonlight: there is NO moon, no moon glitter, no stars, no blue tint anywhere; the sky is flat dark gray and the cold sea is dark gray with subtle wave texture. Viewed from a low vantage just above sea level, at a standoff distance of a few hundred meters. {BOAT[0].upper() + BOAT[1:]}, seen side-on in the center of frame running left to right: the hull and engines white-hot, a bright wake behind, the crew as warm shapes. The sea is dark gray with texture, the horizon faint. Exactly the same white-hot look as the second attached image. No overlay graphics, crosshairs or text."""),
    'a10b': ("Eyes on — standoff", f"""
Night, moonlit open sea with moderate chop. In the midground right, {BOAT}, running fast left to right, dark against the moon glitter. In the left foreground, Marlin paces it at a standoff distance of a few hundred meters, HULL-BORNE: the hull sits IN the water like a boat, the waterline running along its darker gray band, the strut hidden under the surface and not visible, NOT up on the foil, no gap between hull and water, a modest bow wave and wake, steady and low. Far in the background on the boat's other flank, a second identical gray Marlin, also hull-borne, small and indistinct. Camera: 50mm low at water level just behind Marlin's quarter, Marlin sharp. Mood: calm discipline, watching, not letting go. Same boat as the second attached image."""),
}

# Extra continuity references: earlier frames attached after the reference sheet.
CONTINUITY = {'a03': ['a01'], 'a07': ['a06'], 'a09': ['a06'], 'a10a': ['a03'], 'a10b': ['a01']}


def prompt_for(fid):
    title, comp = FRAMES[fid]
    return f"{CINEMATOGRAPHY}\n\n{PRODUCT}\n\nSHOT {fid.upper()} — {title.upper()}. COMPOSITION, CAMERA AND LIGHTING FOR THIS FRAME:\n{comp.strip()}"


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
