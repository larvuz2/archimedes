"""Head-to-head narration test. Absolute 1-10 ratings from the listening model barely move (it scored the v4 read the
client called flat as high as the new takes), so each take is compared directly with a reference read, in both orders
(the model has a position bias), separated by a short tone.

  python3 scripts/vo_ab_v5.py REFERENCE.wav TAKE [TAKE ...]
"""
import os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_describe import describe

Q = ("Two different voice-over takes are played one after the other, separated by a short beep. Judge only the voice performance for an "
     "intense, urgent product-film trailer. Which take has MORE emotion, urgency and intensity (drive, weight, conviction)? Be decisive. "
     "Answer exactly on separate lines: WINNER: first or second / MARGIN: 1-10 (how much more intense; 1 = barely, 10 = night and day) / "
     "FIRST: five words describing the first delivery / SECOND: five words describing the second delivery / NATURAL_SECOND: 1-10 / ISSUES_SECOND: none or problems (glitches, robotic, shouting, mispronounced words)")


def pair(a, b):
    out = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a, '-f', 'lavfi', '-t', '0.25', '-i', 'anullsrc=r=44100:cl=mono', '-f', 'lavfi', '-t', '0.35',
                    '-i', 'sine=f=1000:r=44100', '-f', 'lavfi', '-t', '0.6', '-i', 'anullsrc=r=44100:cl=mono', '-i', b, '-filter_complex',
                    '[0]aresample=44100,aformat=channel_layouts=mono[a];[4]aresample=44100,aformat=channel_layouts=mono[b];[2]volume=0.15[t];'
                    '[a][1][t][3][b]concat=n=5:v=0:a=1', out], check=True)
    return out


def judge(ref, take):
    res = {}
    for order in ('take_second', 'take_first'):
        p = pair(ref, take) if order == 'take_second' else pair(take, ref)
        txt = describe(p, Q)
        os.remove(p)
        w = re.search(r'WINNER\W+(first|second)', txt, re.I)
        m = re.search(r'MARGIN\W+(\d+)', txt)
        win = w.group(1).lower() if w else '?'
        take_won = (win == 'second') if order == 'take_second' else (win == 'first')
        res[order] = (take_won, int(m.group(1)) if m else 0, txt)
    # +margin when the take wins, -margin when the reference wins; averaged over both orders
    score = sum((mg if won else -mg) for won, mg, _ in res.values()) / 2
    desc = re.search(r'SECOND\W+(.+)', res['take_second'][2])
    issues = re.search(r'ISSUES_SECOND\W+(.+)', res['take_second'][2])
    return take, score, [r[0] for r in res.values()], (desc.group(1)[:60] if desc else ''), (issues.group(1)[:90] if issues else '')


if __name__ == '__main__':
    ref, takes = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(lambda t: judge(ref, t), takes))
    for take, score, wins, desc, issues in sorted(rows, key=lambda r: -r[1]):
        print(f'{os.path.basename(take):34s} vs ref {score:+5.1f}  wins {wins}  | {desc} | issues: {issues}')
