"""Score narration takes for emotion / urgency / intensity, since nobody listens during generation.

Three independent reads per clip:
  1. a listening model (fal-ai/audio-understanding) rates EMOTION, URGENCY, INTENSITY, EPIC, NATURAL 1-10 and names artifacts
     (asked twice, averaged);
  2. acoustics: pitch movement (semitone spread), loudness dynamics, vocal effort (spectral centroid), pace;
  3. Whisper transcript, to catch wrong or garbled words.

  /opt/venv-audio/bin/python scripts/vo_rate_v5.py OUT.json CLIP [CLIP ...]
"""
import json, re, sys, os
from concurrent.futures import ThreadPoolExecutor
import numpy as np, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_describe import describe

RUBRIC = ("This is a voice-over narration take for an intense defence-technology product film (a movie-trailer style spot). "
          "Judge ONLY the voice performance. Rate each 1-10 where 10 is best for an epic, urgent, powerful trailer read, and be strict "
          "(a flat, calm, audiobook-style read scores 3-4): EMOTION (how much feeling), URGENCY (sense of time pressure and drive), "
          "INTENSITY (power, weight, force), EPIC (would it fit a blockbuster trailer), NATURAL (sounds like a real human actor, no robotic "
          "or synthetic artifacts). Answer exactly in this format on separate lines: EMOTION: n / URGENCY: n / INTENSITY: n / EPIC: n / "
          "NATURAL: n / ARTIFACTS: none or a short description / WORDS: the exact words you hear.")


def llm(path):
    scores = []
    for _ in range(2):
        try:
            txt = describe(path, RUBRIC)
        except Exception as e:
            txt = f'ERROR {e}'
        d = {k: float(v) for k, v in re.findall(r'(EMOTION|URGENCY|INTENSITY|EPIC|NATURAL)\W+(\d+(?:\.\d+)?)', txt)}
        art = re.search(r'ARTIFACTS\W+(.+)', txt)
        d['artifacts'] = art.group(1).strip()[:160] if art else '?'
        scores.append(d)
    keys = ('EMOTION', 'URGENCY', 'INTENSITY', 'EPIC', 'NATURAL')
    out = {k: float(np.mean([s[k] for s in scores if k in s])) if any(k in s for s in scores) else None for k in keys}
    out['artifacts'] = ' | '.join(s['artifacts'] for s in scores)
    return out


def acoustics(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    f0, vflag, _ = librosa.pyin(y, fmin=55, fmax=400, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    st = 12 * np.log2(f0 / np.median(f0)) if len(f0) else np.array([0.0])
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    db = 20 * np.log10(rms + 1e-6)
    voiced = db > db.max() - 30
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=1024, hop_length=256)[0]
    return dict(dur=round(len(y) / sr, 2), f0_med=round(float(np.median(f0)) if len(f0) else 0, 1),
                pitch_spread_st=round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2),
                loud_dyn_db=round(float(np.percentile(db[voiced], 95) - np.percentile(db[voiced], 20)), 1),
                effort_hz=round(float(np.mean(cent[voiced])), 0), voiced_frac=round(float(voiced.mean()), 2))


def transcribe(paths):
    import torch
    from transformers import pipeline
    torch.set_num_threads(2)
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-medium.en', device='cpu')
    return {p: asr(p)['text'].strip() for p in paths}


if __name__ == '__main__':
    out, paths = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(6) as ex:
        rates = dict(zip(paths, ex.map(llm, paths)))
    words = transcribe(paths)
    rows = []
    for p in paths:
        r = dict(clip=os.path.basename(p), **rates[p], **acoustics(p), words=words[p])
        k = [r[x] for x in ('EMOTION', 'URGENCY', 'INTENSITY', 'EPIC') if r.get(x) is not None]
        r['score'] = round(float(np.mean(k)), 2) if k else 0
        rows.append(r)
    rows.sort(key=lambda r: -r['score'])
    json.dump(rows, open(out, 'w'), indent=1)
    for r in rows:
        print(f"{r['clip']:34s} score {r['score']:4.1f}  E{r['EMOTION']} U{r['URGENCY']} I{r['INTENSITY']} EP{r['EPIC']} N{r['NATURAL']}  "
              f"pitch {r['pitch_spread_st']:4.1f}st dyn {r['loud_dyn_db']:4.1f}dB effort {r['effort_hz']:5.0f}Hz {r['dur']:4.1f}s | {r['words']}")
        if r['artifacts'] and r['artifacts'].lower().replace('|', '').replace('none', '').strip(' .'):
            print('    artifacts:', r['artifacts'])
