"""v5 score (Storyboard V7): same sound as the approved v4 score (dark hybrid trailer, 104 BPM, rhythm-driven), restructured
to the new story: urgent open, a sinking beat, relief, action, then the payoff of the stop. ElevenLabs Music on fal.

  python3 scripts/generate_music_v5.py 4        # 4 candidates -> public/audio/v5/candidates/music_N.mp3

Sections are whole bars at 104 BPM (one bar = 2.31 s), so the edit can cut on the music's own grid:
  0:00 pulse from frame one · 0:04.6 tightens (radar) · 0:09.2 sinks to silence (no end game) · 0:13.8 one held tone, rebuild
  0:18.5 kick on the lift · 0:30.0 builds (stop authorized) · 0:34.6 full power (pass, net away) · 0:41.5 chokes and dies
  0:46.2 hold, relief · 0:50.8 resolve, three hits (Intercept. Surveil. Stop.) · 0:55.4 rings out to silence (end card)
"""
import json, os, pathlib, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v5/candidates'
BPM = 104
BAR = 4 * 60000 / BPM  # ms

SECTIONS = [  # (name, bars, styles+, styles-)
    ('Hard pulse', 2, ['hard driving pulse from the very first beat', 'pounding low drums', 'urgent', 'gritty string ostinato', 'menacing'],
     ['quiet intro', 'fade in', 'slow build', 'melody']),
    ('Tightens', 2, ['tense', 'tighter', 'ticking hi-hat pulse', 'filtered drums', 'rising tension', 'radar-like electronic pulse'], ['melody', 'bright', 'release']),
    ('Sinking', 2, ['sinking', 'descending low strings', 'the rhythm falls away', 'losing energy', 'dread', 'drains to near silence by the end'],
     ['drums groove', 'build', 'hits', 'bright']),
    ('Silence and held tone', 2, ['near silence', 'one single low held tone', 'suspense', 'a riser swells in the last two beats'],
     ['drums', 'groove', 'melody', 'busy']),
    ('Kick in', 5, ['explosive downbeat hit on the first beat', 'full driving drums from the first beat', 'aggressive low string ostinato', 'relentless momentum',
                    'urgent', 'powerful'], ['quiet', 'soft', 'slow build']),
    ('Builds', 2, ['tension build', 'snare roll', 'rising', 'stacking intensity', 'riser into a massive hit'], ['release', 'quiet', 'melody']),
    ('Full power', 3, ['massive hit on the first beat', 'most aggressive section', 'pounding taiko and industrial drums', 'distorted brass braams',
                       'relentless', 'full force'], ['quiet', 'breakdown', 'soft', 'heroic']),
    ('Chokes', 2, ['heavy hits that stutter and choke', 'the drive collapses after the first bar', 'stops dead', 'then near silence'],
     ['groove continues', 'build', 'melody']),
    ('Hold', 2, ['quiet low pulse returns', 'controlled tension', 'calm power', 'slowly building toward the finale'], ['loud', 'drums groove', 'melody', 'happy']),
    ('Resolve', 2, ['score resolves', 'three massive hits, one every two beats', 'huge low braams', 'powerful final statement'],
     ['groove', 'fade out', 'heroic', 'triumphant']),
    ('Tail', 2, ['the last hit rings out', 'long dark reverb tail', 'silence'], ['new theme', 'drums', 'melody', 'groove']),
]
PLAN = {
    'positive_global_styles': ['aggressive dark hybrid trailer music', 'menacing', 'powerful', 'relentless', 'modern military action film',
                               f'{BPM} BPM', 'pounding taiko war drums', 'industrial distorted percussion', 'distorted low brass braams',
                               'gritty driving string ostinato', 'heavy sub bass drops', 'rhythm-driven, no melody', 'instrumental', 'minor key',
                               'punchy modern mix'],
    'negative_global_styles': ['vocals', 'choir', 'singing', 'lyrics', 'spoken word', 'happy', 'uplifting', 'heroic theme', 'triumphant', 'soaring melody',
                               'hopeful', 'major key', 'pop', 'EDM', 'guitar solo', 'jazz', 'lo-fi'],
    'sections': [dict(section_name=n, duration_ms=int(round(b * BAR)), lines=[], positive_local_styles=p, negative_local_styles=neg) for n, b, p, neg in SECTIONS],
}
PLAN['sections'][-1]['duration_ms'] += 60000 - sum(s['duration_ms'] for s in PLAN['sections'])


def gen(i):
    body = dict(composition_plan=PLAN, respect_sections_durations=True, output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/music', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=900))
    except urllib.error.HTTPError as e:
        return i, f'ERROR {e.code} {e.read().decode()[:300]}'
    url = res['audio']['url'] if 'audio' in res else res['audio_file']['url']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'music_{i}.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
    return i, 'ok'


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT.parent / 'music_plan.json').write_text(json.dumps(PLAN, indent=1))
    print('section starts (s):', [round(sum(s['duration_ms'] for s in PLAN['sections'][:k]) / 1000, 2) for k in range(len(PLAN['sections']) + 1)])
    with ThreadPoolExecutor(4) as ex:
        for i, st in ex.map(gen, range(start, start + n)):
            print('candidate', i, st, flush=True)
