"""(Storyboard V5 plan) Generate the score through fal.ai (ElevenLabs Music) with a section plan locked to the edit.

The plan's section boundaries match src/timeline.ts:
  0.0-14.4  tension: dark pulse, ticking, ends on a hard stop (the "gap")
 14.4-18.6  hush under "Archimedes Freight presents... Marlin" (music almost gone)
 18.6-36.4  lift: positive, confident build starts right after "Marlin"
 36.4-46.4  full: biggest, driving, still controlled
 46.4-55.4  recap: three big hits on "Get there / See it / Stay on it", sustain
 55.4-60.0  resolve: warm final chord, one last hit, tail
Writes public/audio/music/score.mp3. Needs FAL_KEY.
"""
import json, os, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/music'

PLAN = {
    'positive_global_styles': [
        'tense modern cinematic score', 'hybrid electronic and orchestral', 'pulsing analog synth bass',
        'taut string ostinato', 'deep cinematic percussion', 'serious, professional, confident',
        'clean modern mix', 'instrumental', '120 bpm'],
    'negative_global_styles': ['vocals', 'choir', 'lyrics', 'rap', 'EDM drop', 'dubstep', 'cheesy', 'lo-fi', 'jazz'],
    'sections': [
        {'section_name': 'Hard pulse', 'duration_ms': 10000, 'lines': [],
         'positive_local_styles': ['hard urgent pulse from the first frame', 'driving low synth bass', 'tightening',
                                   'emergency'], 'negative_local_styles': ['melody', 'major key']},
        {'section_name': 'Sinking', 'duration_ms': 6000, 'lines': [],
         'positive_local_styles': ['sinking feeling', 'descending', 'thinning out', 'drops to complete silence at the end'],
         'negative_local_styles': ['drums', 'major key']},
        {'section_name': 'Held tone', 'duration_ms': 4000, 'lines': [],
         'positive_local_styles': ['one single held soft synth tone in near silence', 'still', 'hopeful'],
         'negative_local_styles': ['drums', 'percussion', 'rhythm']},
        {'section_name': 'Pulse returns', 'duration_ms': 3400, 'lines': [],
         'positive_local_styles': ['quiet pulse returns underneath', 'anticipation', 'rising'],
         'negative_local_styles': ['loud', 'big drums']},
        {'section_name': 'Kick in', 'duration_ms': 16600, 'lines': [],
         'positive_local_styles': ['score kicks in hard on the first beat', 'driving', 'confident', 'propulsive',
                                   'big cinematic drums', 'rising strings', 'speed you can feel'],
         'negative_local_styles': ['dark horror', 'chaotic']},
        {'section_name': 'Steady watch', 'duration_ms': 6000, 'lines': [],
         'positive_local_styles': ['steady', 'disciplined', 'sustained tension under control', 'lighter drums'],
         'negative_local_styles': ['big hits']},
        {'section_name': 'Broaden and resolve', 'duration_ms': 10000, 'lines': [],
         'positive_local_styles': ['score broadens', 'warm resolving', 'relief', 'three big orchestral hits near the end, one second apart'],
         'negative_local_styles': ['dark']},
        {'section_name': 'Out', 'duration_ms': 4000, 'lines': [],
         'positive_local_styles': ['final sustained chord fading to silence'],
         'negative_local_styles': ['new theme', 'drums']},
    ],
}

# Act 2-3 cue (laid from 0:20). Assembled with the Act 1 part of score-v2 in src/audio.ts.
PLAN_ACT2 = {
    'positive_global_styles': PLAN['positive_global_styles'],
    'negative_global_styles': PLAN['negative_global_styles'],
    'sections': [
        {'section_name': 'Pulse returns', 'duration_ms': 3400, 'lines': [],
         'positive_local_styles': ['quiet low synth pulse underneath', 'anticipation', 'building'],
         'negative_local_styles': ['drums', 'loud']},
        {'section_name': 'Kick in and drive', 'duration_ms': 16600, 'lines': [],
         'positive_local_styles': ['full score kicks in hard on the first beat', 'driving propulsive drums', 'rising strings',
                                   'confident', 'speed you can feel'], 'negative_local_styles': ['quiet', 'fade', 'silence']},
        {'section_name': 'Steady watch', 'duration_ms': 6000, 'lines': [],
         'positive_local_styles': ['steady disciplined pulse', 'sustained tension under control'],
         'negative_local_styles': ['silence', 'fade out']},
        {'section_name': 'Broaden and resolve', 'duration_ms': 10000, 'lines': [],
         'positive_local_styles': ['score broadens', 'warm', 'relief', 'resolving', 'big and confident'],
         'negative_local_styles': ['dark', 'silence']},
        {'section_name': 'Final chord', 'duration_ms': 4000, 'lines': [],
         'positive_local_styles': ['final sustained resolving chord'], 'negative_local_styles': ['new theme']},
    ],
}

if __name__ == '__main__':
    import sys
    if '--act2' in sys.argv:
        PLAN, name = PLAN_ACT2, 'score-v2-act2'
    else:
        name = 'score-v2'
    body = dict(composition_plan=PLAN, respect_sections_durations=True,
                output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/music', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=900))
    OUT.mkdir(parents=True, exist_ok=True)
    url = res['audio']['url'] if 'audio' in res else res['audio_file']['url']
    (OUT / f'{name}.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
    (OUT / f'{name}.plan.json').write_text(json.dumps(PLAN, indent=1))
    print(f'wrote public/audio/music/{name}.mp3')
