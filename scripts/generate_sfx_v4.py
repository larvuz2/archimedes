"""v4 sound-effect sources from ElevenLabs Sound Effects (fal). Real-world textures plus trailer one-shots.
Every clip must pass scripts/audio_qc.py (no speech / scream-like sound) before it is used in the mix.
Prompts deliberately avoid words that describe voices (the v2.0 'screaming outboards' lesson).

  python3 scripts/generate_sfx_v4.py            # all -> public/audio/v4/sfx_src/<id>.mp3
  python3 scripts/generate_sfx_v4.py gofast run # redo some
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v4/sfx_src'
SFX = {
    # real-world textures
    'ocean_night': (8.0, 'Wide open sea ambience at night, soft steady wash of small waves, gentle breeze, natural field recording'),
    'gofast': (6.0, 'Powerful speedboat with twin outboard motors racing at full throttle across choppy sea, hull pounding on waves, heavy water spray, recorded from alongside'),
    'fan_spool': (3.5, 'Large electric ducted fan turbine spooling up from standstill to full power, rising mechanical whine and rushing air'),
    'passby': (2.5, 'Fast boat rushing past the microphone at very high speed, sudden loud whoosh of engine and water spray, doppler effect'),
    'run': (8.0, 'Steady roar of a high speed hydrofoil boat, powerful turbine engine, strong wind rush and hissing water spray, constant'),
    'splash': (2.5, 'Heavy boat hull dropping into the sea with one big deep water splash'),
    'idle': (8.0, 'Boat engine at a low idle rumble, water slapping against the hull, calm sea, nobody around'),
    'underwater': (4.0, 'Deep muffled underwater rumble, low drone, distant engine heard from below the surface'),
    # trailer sound design
    'impact': (3.0, 'Deep cinematic trailer impact, huge sub bass boom with a short metallic tail'),
    'braam': (3.0, 'Aggressive cinematic braam, distorted low brass blast, dark and powerful, single hit'),
    'whoosh': (1.2, 'Fast cinematic whoosh, single quick swoosh passing by'),
    'riser': (2.4, 'Tense cinematic riser, noise and tone rising in pitch and intensity to a peak, then cut'),
    'suck': (1.6, 'Reverse cymbal swell sucking in to silence, cinematic transition'),
    'sonar': (2.5, 'Single deep sonar ping with long underwater echo'),
}


def gen(sid):
    dur, text = SFX[sid]
    body = dict(text=text, duration_seconds=dur, prompt_influence=0.55, output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/sound-effects/v2', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=300))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{sid}.mp3').write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    return sid


if __name__ == '__main__':
    ids = sys.argv[1:] or list(SFX)
    with ThreadPoolExecutor(5) as ex:
        for s in ex.map(gen, ids):
            print('wrote', s, flush=True)
