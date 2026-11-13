"""Audio QC: scan clips (or a finished mix) for human vocal sounds with an AudioSet classifier.

Nobody listens while audio is generated, so every clip is checked here before it goes in the mix.
Model: MIT/ast-finetuned-audioset-10-10-0.4593 (527 AudioSet classes), run on sliding windows.

  /opt/venv-audio/bin/python scripts/audio_qc.py public/audio/sfx/*.mp3
  /opt/venv-audio/bin/python scripts/audio_qc.py --window 2 --hop 1 review/marlin-animatic-v3.0.mp4

Exit code 1 if any clip is flagged (unless --no-fail).
"""
import argparse, json, subprocess, sys
import numpy as np
import torch
from transformers import ASTFeatureExtractor, ASTForAudioClassification

MODEL = 'MIT/ast-finetuned-audioset-10-10-0.4593'
# Anything a viewer could hear as a person. Radio chatter is deliberately excluded from the mix too.
VOCAL = ['Speech', 'Male speech, man speaking', 'Female speech, woman speaking', 'Child speech, kid speaking',
         'Conversation', 'Narration, monologue', 'Babbling', 'Shout', 'Bellow', 'Whoop', 'Yell', 'Battle cry',
         'Children shouting', 'Screaming', 'Whispering', 'Laughter', 'Crying, sobbing', 'Baby cry, infant cry',
         'Whimper', 'Wail, moan', 'Sigh', 'Singing', 'Choir', 'Yodeling', 'Chant', 'Mantra', 'Child singing',
         'Synthetic singing', 'Rapping', 'Humming', 'Groan', 'Grunt', 'Gasp', 'Pant', 'Human voice', 'Vocal music',
         'A capella', 'Chatter', 'Crowd', 'Hubbub, speech noise, speech babble', 'Cheering', 'Opera',
         'Animal', 'Howl', 'Roar', 'Roaring cats (lions, tigers)', 'Growling', 'Whale vocalization']
SCREAM = ['Screaming', 'Shout', 'Yell', 'Bellow', 'Whoop', 'Children shouting', 'Battle cry', 'Wail, moan',
          'Crying, sobbing', 'Baby cry, infant cry', 'Howl']


def load(path, sr=16000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--window', type=float, default=2.0)
    ap.add_argument('--hop', type=float, default=1.0)
    ap.add_argument('--threshold', type=float, default=0.15, help='flag if any vocal class exceeds this probability')
    ap.add_argument('--allow-speech', action='store_true', help='narration expected: only flag scream-like classes')
    ap.add_argument('--no-fail', action='store_true')
    ap.add_argument('--threads', type=int, default=1, help='CPU threads (keep low while renders are running)')
    ap.add_argument('--json', help='write full report here')
    a = ap.parse_args()

    torch.set_num_threads(max(1, a.threads))
    fe = ASTFeatureExtractor.from_pretrained(MODEL)
    model = ASTForAudioClassification.from_pretrained(MODEL).eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    watch = SCREAM if a.allow_speech else VOCAL
    widx = [labels.index(l) for l in watch if l in labels]

    report, bad = {}, False
    for path in a.files:
        x = load(path)
        sr = 16000
        if len(x) < sr:  # very short clips: pad with silence so the model has a full window
            x = np.concatenate([x, np.zeros(sr - len(x), dtype=np.float32)])
        win, hop = int(a.window * sr), int(a.hop * sr)
        starts = list(range(0, max(1, len(x) - win + 1), hop)) or [0]
        rows = []
        for s in starts:
            seg = x[s:s + win]
            if np.sqrt(np.mean(seg ** 2) + 1e-12) < 1e-4:  # silence
                continue
            inp = fe(seg, sampling_rate=sr, return_tensors='pt')
            with torch.no_grad():
                p = torch.sigmoid(model(**inp).logits)[0].numpy()
            top = [(labels[i], float(p[i])) for i in np.argsort(-p)[:4]]
            wi = max(widx, key=lambda i: p[i])
            rows.append(dict(t=s / sr, top=top, worst=(labels[wi], float(p[wi]))))
        worst = max(rows, key=lambda r: r['worst'][1]) if rows else None
        flagged = bool(worst and worst['worst'][1] >= a.threshold)
        bad |= flagged
        report[path] = dict(flagged=flagged, worst=worst, windows=rows)
        name = path.split('/')[-1]
        if worst is None:
            print(f'{name:34s} (silent)')
            continue
        # most common top label across windows
        tops = {}
        for r in rows:
            for l, v in r['top'][:2]:
                tops[l] = max(tops.get(l, 0), v)
        summary = ', '.join(f'{l} {v:.2f}' for l, v in sorted(tops.items(), key=lambda kv: -kv[1])[:4])
        mark = 'FLAG' if flagged else 'ok  '
        print(f"{mark} {name:30s} worst vocal: {worst['worst'][0]} {worst['worst'][1]:.2f} @ {worst['t']:.0f}s | hears: {summary}")
        if flagged:
            for r in rows:
                if r['worst'][1] >= a.threshold:
                    print(f"       {r['t']:5.1f}s  {r['worst'][0]} {r['worst'][1]:.2f}   (top: {r['top'][0][0]} {r['top'][0][1]:.2f})")
    if a.json:
        json.dump(report, open(a.json, 'w'), indent=1)
    sys.exit(1 if bad and not a.no_fail else 0)


if __name__ == '__main__':
    main()
