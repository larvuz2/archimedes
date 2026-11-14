"""v4 score: original music in the tone of the client's reference film (about 104 BPM, dark, aggressive,
building), generated with ElevenLabs Music on fal. Sections follow the approved new structure, on a bar grid.

  python3 scripts/generate_music_v4.py 3        # make 3 candidates -> public/audio/v4/candidates/music_N.mp3

Reference analysis (docs/reference-analysis.md): 103 BPM, wall-to-wall, starts dark/low, ignition hit, steady
on-beat drive, a brief drop-out, then climbs to its biggest hit as the end emblem lands.
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v4/candidates'
BPM = 104
BAR = 4 * 60000 / BPM  # ms

def bars(n):
    return int(round(n * BAR))

SECTIONS = [  # (name, bars, styles+, styles-)
    ('Dark intro', 2, ['dark low drone', 'ominous', 'one deep distant impact', 'sparse', 'tension'], ['drums groove', 'melody', 'bright']),
    ('Predator waiting', 3, ['near silence', 'slow heavy sub pulse like a heartbeat', 'menacing calm', 'low strings holding one note',
                             'rising riser at the very end'], ['drums groove', 'busy', 'bright', 'melody']),
    ('Ignition', 4, ['explosive downbeat hit on the first beat', 'pounding war drums at full force from the first beat', 'aggressive low string ostinato', 'driving', 'urgent'], ['quiet', 'soft', 'slow build']),
    ('Full power', 5, ['full aggressive drive', 'pounding drums', 'distorted low brass braams', 'relentless momentum', 'intensity climbing'], ['quiet', 'breakdown', 'soft']),
    ('Heavy', 6, ['heavy half-time groove', 'huge slow drum hits', 'menacing', 'controlled power', 'building back up through the section'], ['bright', 'happy']),
    ('Finale', 3, ['most aggressive moment', 'everything at full force', 'three massive braam hits', 'ends on one enormous final hit'], ['fade out', 'quiet', 'heroic']),
    ('Tail', 3, ['the final hit rings out', 'deep low booms far apart', 'dark resolve', 'long reverb tail to silence'], ['new theme', 'drums groove', 'melody']),
]
PLAN = {
    'positive_global_styles': ['aggressive dark hybrid trailer music', 'menacing', 'powerful', 'relentless', 'modern military action film',
                               f'{BPM} BPM', 'pounding taiko war drums', 'industrial distorted percussion', 'distorted low brass braams',
                               'gritty driving string ostinato', 'heavy sub bass drops', 'rhythm-driven, no melody', 'instrumental', 'minor key',
                               'punchy modern mix'],
    'negative_global_styles': ['vocals', 'choir', 'singing', 'lyrics', 'spoken word', 'happy', 'uplifting', 'heroic theme', 'triumphant', 'soaring melody',
                               'hopeful', 'emotional', 'major key', 'pop', 'EDM', 'guitar solo', 'jazz', 'lo-fi'],
    'sections': [dict(section_name=n, duration_ms=bars(b), lines=[], positive_local_styles=p, negative_local_styles=neg) for n, b, p, neg in SECTIONS],
}
# make the plan exactly 60 s
PLAN['sections'][-1]['duration_ms'] += 60000 - sum(s['duration_ms'] for s in PLAN['sections'])


def gen(i):
    body = dict(composition_plan=PLAN, respect_sections_durations=True, output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/music', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=900))
    url = res['audio']['url'] if 'audio' in res else res['audio_file']['url']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'music_{i}.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
    return i


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    (OUT.parent / 'music_plan.json').write_text(json.dumps(PLAN, indent=1))
    print('section starts (s):', [round(sum(s['duration_ms'] for s in PLAN['sections'][:k]) / 1000, 2) for k in range(len(PLAN['sections']) + 1)])
    with ThreadPoolExecutor(3) as ex:
        for i in ex.map(gen, range(start, start + n)):
            print('wrote candidate', i, flush=True)
