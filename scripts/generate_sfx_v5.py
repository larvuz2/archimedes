"""v5 sound-effect sources for Storyboard V7's new moments (the stop), from ElevenLabs Sound Effects (fal).
The v4 sources (public/audio/v4/sfx_src) are reused for the rest. Every clip must pass scripts/audio_qc.py.
Prompts never describe voices: the storyboard's "outboards scream" is written here as engines bogging and stalling.

  python3 scripts/generate_sfx_v5.py            # all -> public/audio/v5/sfx_src/<id>.mp3
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v5/sfx_src'
SFX = {
    'net_launch': (1.5, 'Compressed-air launcher firing outdoors at sea, one sharp heavy pneumatic thump with a short burst of hissing air'),
    'net_slap': (2.0, 'A long floating rope line with plastic floats slapping down onto the sea surface in a fast ripple of splashes'),
    'engines_bog': (4.5, 'Two big outboard boat motors at full throttle suddenly bogging down, sputtering, choking and stalling as the propellers jam, the motors cut out completely, then only water lapping against the hull'),
    'prop_jam': (2.5, 'Underwater, muffled: a boat propeller churning and jamming on rope, bubbling and grinding, slowing to a stop'),
    'partner': (6.0, 'Distant patrol boat engine approaching across open water at night, a low steady diesel rumble slowly growing louder'),
    'hull_slap': (6.0, 'Small waves slapping gently against the hull of a boat sitting still on the sea at night, water lapping, no engine'),
    # 'outboards_swerve' was dropped: its take had a scream in it (listening check). The swerve uses v4's checked go-fast clip.
}


def gen(sid):
    dur, text = SFX[sid]
    body = dict(text=text, duration_seconds=dur, prompt_influence=0.55, output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/sound-effects/v2', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        return sid, f'ERROR {e.code} {e.read().decode()[:200]}'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{sid}.mp3').write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    return sid, 'ok'


if __name__ == '__main__':
    ids = sys.argv[1:] or list(SFX)
    with ThreadPoolExecutor(5) as ex:
        for s, st in ex.map(gen, ids):
            print(s, st, flush=True)
