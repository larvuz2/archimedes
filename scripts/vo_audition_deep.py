"""Option B narrator: a deeper, epic voice with the same urgency as v5.0's read. Auditions the same two lines across deep
voices and directions; scored by pitch (deepness), head-to-head urgency against the v5.0 read, and transcription.

  python3 scripts/vo_audition_deep.py OUTDIR
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

TEXT = 'Tasked... the nearest two close... fifty miles in thirty minutes! ... And stop it dead in the water!'
DIRS = {
    'deep': '[epic movie trailer narrator, very deep booming voice, intense, rising urgency]',
    'low': '[deep, low and resonant, powerful, urgent, epic]',
}
# ElevenLabs premade voices by name, plus deep legacy voices by id (Adam, Arnold, Clyde, Josh)
EL = [(v, d) for v in ('Brian', 'Bill', 'George', 'pNInz6obpgDQGcFmaJgB', 'VR6AewLTigWG4xSOukaG', '2EiwWnXFnvU5JabPnv8n', 'TxGEqnHWrfWFTfGW9XjX') for d in DIRS]
MM = [('Deep_Voice_Man', 'angry', -2), ('Deep_Voice_Man', 'neutral', -3), ('Imposing_Manner', 'angry', -3), ('Determined_Man', 'angry', -3)]
NAMES = {'pNInz6obpgDQGcFmaJgB': 'Adam', 'VR6AewLTigWG4xSOukaG': 'Arnold', '2EiwWnXFnvU5JabPnv8n': 'Clyde', 'TxGEqnHWrfWFTfGW9XjX': 'Josh'}


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=300))


def el(job):
    voice, d = job
    res = post('https://fal.run/fal-ai/elevenlabs/tts/eleven-v3', dict(text=f'{DIRS[d]} {TEXT}', voice=voice, stability=0.0))
    return f'el_{NAMES.get(voice, voice)}_{d}', res['audio']['url']


def mm(job):
    voice, emo, pitch = job
    body = dict(text=TEXT.replace('...', ','), voice_setting=dict(voice_id=voice, speed=0.95, vol=1.0, pitch=pitch, emotion=emo), output_format='url')
    res = post('https://fal.run/fal-ai/minimax/speech-02-hd', body)
    return f'mm_{voice}_{emo}_p{pitch}', res['audio']['url']


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    def run(fj):
        f, j = fj
        try:
            name, url = f(j)
            (out / f'{name}.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
            return name, 'ok'
        except urllib.error.HTTPError as e:
            return str(j), f'ERROR {e.code} {e.read().decode()[:160]}'
        except Exception as e:
            return str(j), f'ERROR {e}'
    with ThreadPoolExecutor(6) as ex:
        for name, st in ex.map(run, [(el, j) for j in EL] + [(mm, j) for j in MM]):
            print(name, st, flush=True)
