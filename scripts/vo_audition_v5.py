"""v5 narration auditions. Client note on v4: "the VO is too flat - needs more emotion / urgency / intensity".
Same two test lines through several voices, directions and expressiveness settings; scripts/vo_rate_v5.py scores them.

  python3 scripts/vo_audition_v5.py OUTDIR
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

TEXT = 'Tasked... the nearest two close... fifty miles in thirty minutes! ... And stop it dead in the water!'
DIRS = {
    'urgent': '[urgent] [intense]',
    'trailer': '[epic movie trailer narrator, deep and intense, rising urgency]',
    'command': '[forceful, commanding, driven, every word hits hard]',
}
EL = [  # (voice, direction, stability)
    ('Brian', 'urgent', 0.0), ('Brian', 'trailer', 0.0), ('Brian', 'command', 0.0), ('Brian', 'urgent', 0.3),
    ('Callum', 'urgent', 0.0), ('Callum', 'trailer', 0.0),
    ('Bill', 'urgent', 0.0), ('Bill', 'trailer', 0.0),
    ('Roger', 'urgent', 0.0), ('Roger', 'trailer', 0.0),
    ('Daniel', 'urgent', 0.0), ('Daniel', 'command', 0.0),
]
MM = [('Deep_Voice_Man', 'angry'), ('Imposing_Manner', 'angry'), ('Determined_Man', 'angry'), ('Imposing_Manner', 'surprised')]


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=300))


def el(job):
    voice, d, stab = job
    name = f'el_{voice}_{d}_s{int(stab * 10)}'
    res = post('https://fal.run/fal-ai/elevenlabs/tts/eleven-v3', dict(text=f'{DIRS[d]} {TEXT}', voice=voice, stability=stab))
    return name, res['audio']['url']


def mm(job):
    voice, emo = job
    name = f'mm_{voice}_{emo}'
    body = dict(text=TEXT.replace('...', ','), voice_setting=dict(voice_id=voice, speed=1.0, vol=1.0, pitch=0, emotion=emo),
                output_format='url')
    res = post('https://fal.run/fal-ai/minimax/speech-02-hd', body)
    return name, res['audio']['url']


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(el, j) for j in EL] + [(mm, j) for j in MM]

    def run(fj):
        f, j = fj
        try:
            name, url = f(j)
            (out / f'{name}.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
            return name, 'ok'
        except urllib.error.HTTPError as e:
            return str(j), f'ERROR {e.code} {e.read().decode()[:200]}'
        except Exception as e:
            return str(j), f'ERROR {e}'
    with ThreadPoolExecutor(6) as ex:
        for name, st in ex.map(run, jobs):
            print(name, st, flush=True)
