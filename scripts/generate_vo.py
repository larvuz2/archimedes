"""Generate the narrator through fal.ai (ElevenLabs v3, expressive read).

Lines + direction tags come from src/vo.json. Writes public/audio/vo/<id>.mp3 (trimmed,
leveled to -16 LUFS) and public/audio/vo/<id>.words.json (word timestamps, when returned).
Needs FAL_KEY.

  python3 scripts/generate_vo.py              # all lines
  python3 scripts/generate_vo.py --only vo3   # just some
  python3 scripts/generate_vo.py --voice Bill
"""
import argparse, json, os, pathlib, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/vo'
CFG = json.loads((ROOT / 'src/vo.json').read_text())
ENDPOINTS = {
    'eleven-v3': 'https://fal.run/fal-ai/elevenlabs/tts/eleven-v3',
    'multilingual-v2': 'https://fal.run/fal-ai/elevenlabs/tts/multilingual-v2',
}


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=300))


def clean(src, dest):
    """Trim leading/trailing silence and level to -16 LUFS."""
    trim = 'silenceremove=start_periods=1:start_threshold=-50dB'
    af = f'{trim},areverse,{trim},areverse,loudnorm=I=-16:TP=-1.5:LRA=9,apad=pad_dur=0.05'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', af, '-ar', '44100',
                    '-c:a', 'libmp3lame', '-q:a', '2', str(dest)], check=True)


def gen(line, voice, model):
    text = f"{line.get('direction', '')} {line.get('say', line['text'])}".strip()
    if model == 'eleven-v3':
        body = dict(text=text, voice=voice, stability=0.5, timestamps=True)
    else:
        body = dict(text=line.get('say', line['text']), voice=voice, stability=0.4,
                    similarity_boost=0.8, style=0.5, speed=1.0)
    res = post(ENDPOINTS[model], body)
    raw = OUT / 'raw' / f"{line['id']}.mp3"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    if res.get('timestamps'):
        (OUT / 'raw' / f"{line['id']}.words.json").write_text(json.dumps(res['timestamps'], indent=1))
    clean(raw, OUT / f"{line['id']}.mp3")
    return line['id']


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', default=CFG['voice'])
    ap.add_argument('--model', default=CFG['model'], choices=list(ENDPOINTS))
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    lines = [l for l in CFG['lines'] if not a.only or l['id'] in a.only]
    with ThreadPoolExecutor(4) as ex:
        for i in ex.map(lambda l: gen(l, a.voice, a.model), lines):
            print('wrote', i)
