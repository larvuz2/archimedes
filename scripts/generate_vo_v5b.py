"""Option B narrator for v5.1: a deeper, epic voice with the same urgency. Same lines and splitting as generate_vo_v5.py,
deep directions, several takes per line, for one or more candidate voices.

  python3 scripts/generate_vo_v5b.py 3 Brian Clyde      # -> public/audio/v5/vo_deep/takes/<voice>/
"""
import os, pathlib, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_vo_v5 as G

DEEP = '[epic movie trailer narrator, very deep booming voice, intense, rising urgency]'
TAKES = {
    'A': (DEEP, [('l1a', 'Tasked,'), ('l1b', 'the nearest two close'), ('l1c', 'fifty miles in thirty minutes!')]),
    'B': ('[very deep and low, urgent, driving]', [('l2', 'Put eyes on!')]),
    'C': ('[very deep, forceful, intense, every word hits hard]', [('l3', 'And stop it dead in the water!')]),
    'D': ('[very deep, powerful, resolute]', [('l4', 'Until partners arrive.')]),
    'E': ('[epic movie trailer narrator, very deep booming voice, each word a hammer blow]', [('l5a', 'Intercept.'), ('l5b', 'Surveil.'), ('l5c', 'Stop.')]),
    'F': ('[very deep, epic, final]', [('l6', 'Marlin.')]),
}
VOICE_IDS = {'Clyde': '2EiwWnXFnvU5JabPnv8n', 'Josh': 'TxGEqnHWrfWFTfGW9XjX', 'Adam': 'pNInz6obpgDQGcFmaJgB'}

if __name__ == '__main__':
    n = int(sys.argv[1])
    for voice in sys.argv[2:]:
        G.VOICE = VOICE_IDS.get(voice, voice)
        G.TAKES = TAKES
        G.OUT = pathlib.Path(__file__).resolve().parent.parent / 'public/audio/v5/vo_deep' / voice
        with ThreadPoolExecutor(6) as ex:
            for g, i, st in ex.map(G.gen, [(g, i) for g in TAKES for i in range(1, n + 1)]):
                print(voice, g, i, st, flush=True)
