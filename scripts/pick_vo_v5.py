"""Pick the best take of every v5 narration line.

  1. words: Whisper must hear the line (numbers normalised);
  2. issues: the listening model checks each take for glitches, robotic artefacts, shouting or garbled words;
  3. intensity: among the takes left, keep the one with the most vocal energy for this voice (vocal effort, pitch lift and
     movement, loudness contrast), compared within the same line so the voice itself does not skew it.
Writes public/audio/v5/vo/<line>.wav and public/audio/v5/vo/picks.json.

  /opt/venv-audio/bin/python scripts/pick_vo_v5.py
"""
import json, os, re, shutil, sys, pathlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_describe import describe
from vo_rate_v5 import acoustics, transcribe

ROOT = pathlib.Path(__file__).resolve().parent.parent
VO = ROOT / 'public/audio/v5/vo'
LINES = {'l1a': 'tasked', 'l1b': 'the nearest two close', 'l1ab': 'tasked the nearest two close', 'l1c': 'fifty miles in thirty minutes',
         'l2': 'put eyes on', 'l3': 'and stop it dead in the water', 'l4': 'until partners arrive', 'l5a': 'intercept', 'l5b': 'surveil',
         'l5c': 'stop', 'l6': 'marlin'}
NUM = {'50': 'fifty', '30': 'thirty', '2': 'two', 'too': 'two', 'to': 'two'}
ISSUES = ("This is one line of a voice-over for a product film. Listen for problems only. Answer on separate lines: WORDS: exactly what is said / "
          "GLITCH: yes/no (clicks, warble, robotic or synthetic artefacts, cut-off syllables) / SHOUTING: yes/no (yelling or screaming, not just "
          "intense) / CLEAR: 1-10 (how clearly every word is articulated)")


def norm(s):
    w = re.sub(r"[^a-z0-9 ]", ' ', s.lower()).split()
    return ' '.join(NUM.get(x, x) for x in w)


def check(p):
    try:
        txt = describe(str(p), ISSUES)
    except Exception as e:
        txt = f'ERROR {e}'
    g = re.search(r'GLITCH\W+(yes|no)', txt, re.I)
    sh = re.search(r'SHOUTING\W+(yes|no)', txt, re.I)
    c = re.search(r'CLEAR\W+(\d+)', txt)
    return dict(glitch=(g.group(1).lower() == 'yes') if g else None, shouting=(sh.group(1).lower() == 'yes') if sh else None,
                clear=int(c.group(1)) if c else None)


if __name__ == '__main__':
    takes = sorted((VO / 'takes').glob('l*_*.wav'))
    words = transcribe([str(p) for p in takes])
    with ThreadPoolExecutor(6) as ex:
        issues = dict(zip(takes, ex.map(check, takes)))
    rows = []
    for p in takes:
        line = p.stem.rsplit('_', 1)[0]
        heard = norm(words[str(p)])
        ok_words = heard.replace('two', '').split() == norm(LINES[line]).replace('two', '').split() or heard == norm(LINES[line])
        rows.append(dict(take=p.name, line=line, heard=words[str(p)], ok_words=ok_words, **issues[p], **acoustics(str(p))))
    picks = {}
    for line in sorted({r['line'] for r in rows}):
        rs = [r for r in rows if r['line'] == line]
        z = lambda k: (np.array([r[k] for r in rs]) - np.mean([r[k] for r in rs])) / (np.std([r[k] for r in rs]) + 1e-9)
        energy = z('effort_hz') + 0.6 * z('pitch_spread_st') + 0.6 * z('loud_dyn_db') + 0.8 * z('f0_med')
        for r, e in zip(rs, energy):
            r['energy'] = round(float(e), 2)
            r['eligible'] = r['ok_words'] and r['glitch'] is not True and r['shouting'] is not True and (r['clear'] or 10) >= 7
        good = [r for r in rs if r['eligible']] or [r for r in rs if r['ok_words']] or rs
        best = max(good, key=lambda r: r['energy'])
        picks[line] = best['take']
        for r in sorted(rs, key=lambda r: -r['energy']):
            mark = '*' if r is best else ' '
            print(f"{mark} {r['take']:12s} energy {r['energy']:+5.2f} words {'ok ' if r['ok_words'] else 'BAD'} glitch {r['glitch']} shout {r['shouting']} "
                  f"clear {r['clear']} f0 {r['f0_med']} pitch {r['pitch_spread_st']} effort {r['effort_hz']} {r['dur']}s | {r['heard']}")
    for line, take in picks.items():
        shutil.copy(VO / 'takes' / take, VO / f'{line}.wav')
    json.dump(dict(picks=picks, rows=rows), open(VO / 'picks.json', 'w'), indent=1)
    print(picks)
