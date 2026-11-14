"""v4 narrator: ElevenLabs v3 (fal), stock voice "Brian", directed low / gravelly / calm intensity.
Short declarative lines, in the cadence of the client's reference film. Lines that belong together are
generated in one take (consistent tone) and split on the returned character timestamps.

  python3 scripts/generate_vo_v4.py            # all takes -> public/audio/v4/vo/<id>.wav
  python3 scripts/generate_vo_v4.py B G        # redo some takes
"""
import json, os, pathlib, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v4/vo'
VOICE = 'Brian'
TAKES = {  # take -> (direction, [(id, sentence), ...])
    'A': ('[low, ominous, measured]', [('v01', 'A boat is running dark for the coast.')]),
    'B': ('[low, gravelly, calm, intense]', [('v02', 'Marlin is already out there.'), ('v03', 'Waiting.'), ('v04', 'Always ready.')]),
    'C': ('[low, firm, certain]', [('v05', 'It detects the contact.')]),
    'D': ('[intense, driving, urgent, low]', [('v06', 'The nearest Marlins vector in.'), ('v07', 'Fifty miles in thirty minutes.')]),
    'E': ('[cold, firm, final]', [('v08', 'They isolate the contact.')]),  # 'isolate it' kept being heard as 'isolated'
    'F': ('[steady, resolute, low]', [('v09', 'And they stay on it.'), ('v10', 'Until partners arrive.')]),
    'G': ('[powerful, commanding, low, each word like a hammer blow]', [('v11', 'Detect.'), ('v12', 'Isolate.'), ('v13', 'Surveil.')]),
    'H': ('[deep, final, low]', [('v14', 'Marlin.')]),
}


def split_on_pauses(raw, n):
    """Find the n spoken phrases in a take by its silences (the model's own timestamps are not reliable enough)."""
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(raw), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, dtype=np.float32)
    hop = 160  # 10 ms
    env = np.array([np.sqrt(np.mean(x[i:i + 2 * hop] ** 2) + 1e-12) for i in range(0, len(x) - 2 * hop, hop)])
    db = 20 * np.log10(env / env.max())
    for thr in (-34, -30, -38, -26, -42):
        voiced = db > thr
        segs, start = [], None
        for i, v in enumerate(voiced):
            if v and start is None:
                start = i
            if not v and start is not None:
                segs.append([start, i]); start = None
        if start is not None:
            segs.append([start, len(voiced)])
        merged = []
        for sg in segs:  # join pieces separated by less than 0.28 s (inside a phrase)
            if merged and sg[0] - merged[-1][1] < 28:
                merged[-1][1] = sg[1]
            else:
                merged.append(sg)
        merged = [m for m in merged if m[1] - m[0] > 12]
        if len(merged) == n:
            return [(max(0.0, a * 0.01 - 0.05), b_ * 0.01 + 0.12) for a, b_ in merged]
    raise RuntimeError(f'{raw.name}: expected {n} phrases, found {len(merged)}')


def cut(raw, parts):
    for (vid, _), (a, b_) in zip(parts, split_on_pauses(raw, len(parts))):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-ss', f'{a:.3f}', '-to', f'{b_:.3f}', '-af',
                        'afade=t=in:d=0.012,areverse,afade=t=in:d=0.03,areverse,apad=pad_dur=0.06', '-ar', '48000', '-ac', '1', str(OUT / f'{vid}.wav')], check=True)


def run(take):
    direction, parts = TAKES[take]
    raw = OUT / 'raw' / f'take_{take}.mp3'
    if not RESPLIT:
        text = f'{direction} ' + ' ... '.join(s for _, s in parts)
        body = dict(text=text, voice=VOICE, stability=0.5)
        req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/tts/eleven-v3', data=json.dumps(body).encode(),
                                     headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
        res = json.load(urllib.request.urlopen(req, timeout=300))
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    cut(raw, parts)
    return take, ' | '.join(s for _, s in parts)


RESPLIT = False

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--resplit']
    RESPLIT = '--resplit' in sys.argv  # cut the existing raw takes again without generating
    takes = args or list(TAKES)
    with ThreadPoolExecutor(4) as ex:
        for take, full in ex.map(run, takes):
            print(take, '->', full)
