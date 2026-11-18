"""Option B narrator: head-to-head of deep candidates against the v5.0 narrator on identical lines, both orders (the listening
model favours the second clip), on two questions: deeper and more epic? as urgent and intense?

  python3 scripts/vo_ab_deep.py REFERENCE TAKE [TAKE ...]
"""
import os, re, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_describe import describe
from vo_ab_v5 import pair

Q = ("Two voice-over takes of the same lines play one after the other, separated by a short beep. Judge only the voices. Answer exactly on "
     "separate lines: DEEPER_AND_MORE_EPIC: first or second / DEEP_MARGIN: 1-10 / MORE_URGENT_AND_INTENSE: first or second / URGENCY_MARGIN: 1-10 / "
     "SECOND: five words describing the second voice / SECOND_NATURAL: 1-10 / SECOND_ISSUES: none or problems (glitches, robotic, mispronounced words)")


def judge(ref, take):
    deep = urg = 0.0
    notes = ''
    for order in ('take_second', 'take_first'):
        p = pair(ref, take) if order == 'take_second' else pair(take, ref)
        try:
            txt = describe(p, Q)
        except Exception as e:
            txt = f'ERROR {e}'
        os.remove(p)
        mine = 'second' if order == 'take_second' else 'first'
        for key, mkey in (('DEEPER_AND_MORE_EPIC', 'DEEP_MARGIN'), ('MORE_URGENT_AND_INTENSE', 'URGENCY_MARGIN')):
            w = re.search(key + r'\W+(first|second)', txt, re.I)
            m = re.search(mkey + r'\W+(\d+)', txt)
            v = (int(m.group(1)) if m else 0) * (1 if w and w.group(1).lower() == mine else -1)
            if key.startswith('DEEP'):
                deep += v / 2
            else:
                urg += v / 2
        if order == 'take_second':
            d = re.search(r'SECOND\W+(.+)', txt)
            n = re.search(r'SECOND_NATURAL\W+(\d+)', txt)
            iss = re.search(r'SECOND_ISSUES\W+(.+)', txt)
            notes = f"{d.group(1)[:50] if d else ''} | natural {n.group(1) if n else '?'} | {iss.group(1)[:70] if iss else ''}"
    return take, deep, urg, notes


if __name__ == '__main__':
    ref, takes = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(7) as ex:
        rows = list(ex.map(lambda t: judge(ref, t), takes))
    for take, deep, urg, notes in sorted(rows, key=lambda r: -(r[1] + r[2])):
        print(f'{os.path.basename(take):36s} deeper {deep:+5.1f}  urgency {urg:+5.1f}  | {notes}')
