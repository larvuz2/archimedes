"""Generate scratch VO through fal.ai (ElevenLabs multilingual v2).

Reads the VO lines from src/timeline.ts and writes public/audio/vo/shot-NN.mp3.
Needs FAL_KEY in the environment. Raw downloads go to public/audio/vo/raw/; trimmed and
loudness-leveled copies are what the edit uses.

  python3 scripts/generate_vo.py                 # all shots, default voice
  python3 scripts/generate_vo.py --voice Bill    # another voice
  python3 scripts/generate_vo.py --audition      # one line in several voices -> public/audio/vo/auditions/
"""
import argparse, json, os, re, pathlib, subprocess, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/vo'
ENDPOINT = 'https://fal.run/fal-ai/elevenlabs/tts/multilingual-v2'
# Calm, authoritative, measured: storyboard asks for "not action-movie".
SETTINGS = dict(stability=0.6, similarity_boost=0.75, style=0.1, speed=1.1)
AUDITION_VOICES = ['Brian', 'Bill', 'Eric', 'Chris', 'Daniel', 'Sarah']
AUDITION_LINE = ("Conventional patrols take time to respond, and rough water slows them further. "
                 "Threats don't wait. Archimedes Freight presents Marlin.")


def lines():
    src = (ROOT / 'src/timeline.ts').read_text()
    return [(int(i), vo) for i, vo in re.findall(r"\{id: (\d+),.*?vo: [\"'](.*?)[\"'],\n", src, re.S)]


def tts(text, voice, dest, prev='', nxt=''):
    body = dict(text=text, voice=voice, previous_text=prev, next_text=nxt, **SETTINGS)
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={
        'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    url = json.load(urllib.request.urlopen(req, timeout=180))['audio']['url']
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = dest.parent / 'raw' / dest.name
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(urllib.request.urlopen(url, timeout=180).read())
    clean(raw, dest)
    print('wrote', dest.relative_to(ROOT))


def clean(src, dest):
    """Trim leading/trailing silence and level to -16 LUFS so lines sit evenly in the mix."""
    trim = 'silenceremove=start_periods=1:start_threshold=-50dB'
    af = f'{trim},areverse,{trim},areverse,loudnorm=I=-16:TP=-1.5:LRA=7,apad=pad_dur=0.05'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', af, '-ar', '44100',
                    '-c:a', 'libmp3lame', '-q:a', '2', str(dest)], check=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', default='Brian')
    ap.add_argument('--audition', action='store_true')
    ap.add_argument('--only', type=int, nargs='*', help='shot ids to regenerate')
    ap.add_argument('--clean-only', action='store_true', help='re-run trim/level on existing raw files')
    a = ap.parse_args()
    if a.clean_only:
        for raw in sorted((OUT / 'raw').glob('shot-*.mp3')):
            clean(raw, OUT / raw.name)
    elif a.audition:
        for v in AUDITION_VOICES:
            tts(AUDITION_LINE, v, OUT / 'auditions' / f'{v.lower()}.mp3')
    else:
        L = lines()
        for k, (i, text) in enumerate(L):
            if a.only and i not in a.only:
                continue
            prev = L[k - 1][1] if k else ''
            nxt = L[k + 1][1] if k + 1 < len(L) else ''
            tts(text, a.voice, OUT / f'shot-{i:02d}.mp3', prev, nxt)
