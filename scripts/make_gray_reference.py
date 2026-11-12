"""Make a defense-gray version of the Marlin reference sheet (client fix #05: defense gray, no police white/blue,
no light bar or strobes). Uses GPT Image 2.5 edit on fal. Output: public/assets/models/marlin-reference-sheet-gray.jpg"""
import base64, json, os, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'public/assets/models/marlin-reference-sheet.jpg'
OUT = ROOT / 'public/assets/models/marlin-reference-sheet-gray.jpg'
PROMPT = """Edit this product reference sheet. Keep the exact same six views, camera angles, layout, studio background, lighting, proportions, geometry and every part of the vehicle identical (pod hull, large ducted fan ring with three-blade propeller and spinner, V-shaped tail fin on its pylon, short sensor mast with horizontal sensor bar and thin antenna, single raked hydrofoil strut, panel lines and hatches).
Change ONLY the paint and lights:
- Repaint the entire vehicle in a uniform matte cool slate-gray industrial finish (medium haze gray), with a slightly darker gray band where the blue band was and a dark charcoal underside. No white, no blue anywhere on the vehicle.
- Remove both blue beacon lights completely; the top of the duct ring is smooth gray where they were. No light bar, no strobes, no colored lights.
- Keep the title text "AI REFERENCE SHEET" and the six view labels exactly as they are."""
ref = 'data:image/jpeg;base64,' + base64.b64encode(SRC.read_bytes()).decode()
body = dict(prompt=PROMPT, image_urls=[ref], image_size={'width': 1536, 'height': 1024}, quality='high', output_format='jpeg')
req = urllib.request.Request('https://fal.run/openai/gpt-image-2.5/flare/edit', data=json.dumps(body).encode(),
                             headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=900))
OUT.write_bytes(urllib.request.urlopen(res['images'][0]['url'], timeout=300).read())
print('wrote', OUT.relative_to(ROOT))
