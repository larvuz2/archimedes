"""v5 narrator (Storyboard V7, 27 words). Client note on v4: "the VO is too flat - needs more emotion / urgency / intensity".
Voice chosen by audition (scripts/vo_audition_v5.py, vo_rate_v5.py, vo_ab_v5.py): ElevenLabs v3 "Callum", directed as an epic,
urgent trailer read at the most expressive setting (stability 0). Several takes per line; scripts/pick_vo_v5.py keeps the best.

  python3 scripts/generate_vo_v5.py 4        # 4 takes of every line -> public/audio/v5/vo/takes/
"""
import json, os, pathlib, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_vo_v4 import split_on_pauses

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v5/vo'
VOICE = 'Callum'
EPIC = '[epic movie trailer narrator, deep and intense, rising urgency]'
TAKES = {  # group -> (direction, [(id, words), ...]); lines in one group are spoken in one take and split on the pauses
    'A': (EPIC, [('l1a', 'Tasked,'), ('l1b', 'the nearest two close'), ('l1c', 'fifty miles in thirty minutes!')]),
    'B': ('[intense, urgent, driving]', [('l2', 'Put eyes on!')]),
    'C': ('[forceful, intense, every word hits hard]', [('l3', 'And stop it dead in the water!')]),
    'D': ('[powerful, resolute, intense]', [('l4', 'Until partners arrive.')]),
    'E': ('[epic movie trailer narrator, commanding, each word a hammer blow]', [('l5a', 'Intercept.'), ('l5b', 'Surveil.'), ('l5c', 'Stop.')]),
    'F': ('[deep, epic, final]', [('l6', 'Marlin.')]),
}


def gen(job):
    group, n = job
    direction, parts = TAKES[group]
    raw = OUT / 'takes' / f'{group}_{n}.mp3'
    text = f'{direction} ' + ' ... '.join(w for _, w in parts)
    body = dict(text=text, voice=VOICE, stability=0.0)
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/tts/eleven-v3', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=300))
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    except Exception as e:
        return group, n, f'ERROR {e}'
    try:
        segs = split_on_pauses(raw, len(parts))
    except RuntimeError:
        if group != 'A':
            return group, n, 'ERROR could not split'
        # "Tasked, the nearest two close" often comes as one phrase: keep it whole, the numbers still land on their own
        parts = [('l1ab', 'Tasked, the nearest two close'), ('l1c', parts[2][1])]
        try:
            segs = split_on_pauses(raw, 2)
        except RuntimeError as e:
            return group, n, f'ERROR {e}'
    for (lid, _), (a, b) in zip(parts, segs):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-af',
                        'afade=t=in:d=0.012,areverse,afade=t=in:d=0.04,areverse,apad=pad_dur=0.06', '-ar', '48000', '-ac', '1',
                        str(OUT / 'takes' / f'{lid}_{n}.wav')], check=True)
    return group, n, 'ok'


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    groups = sys.argv[2:] or list(TAKES)
    jobs = [(g, i) for g in groups for i in range(1, n + 1)]
    with ThreadPoolExecutor(6) as ex:
        for g, i, st in ex.map(gen, jobs):
            print(g, i, st, flush=True)
