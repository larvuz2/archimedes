"""Generate the score through fal.ai (ElevenLabs Music) with a section plan locked to the edit.

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
        'cinematic hybrid orchestral trailer score', 'modern defense-technology commercial',
        'pulsing analog synth bass', 'taut string ostinato', 'deep cinematic percussion',
        'heroic but restrained', 'clean modern mix', 'instrumental', '120 bpm'],
    'negative_global_styles': ['vocals', 'choir lyrics', 'rap', 'EDM drop', 'dubstep', 'cheesy', 'lo-fi', 'jazz'],
    'sections': [
        {'section_name': 'Tension', 'duration_ms': 14400, 'lines': [],
         'positive_local_styles': ['dark low synth pulse', 'sparse', 'clock-like ticking percussion building',
                                   'uneasy suspended strings', 'ends on an abrupt hard stop'],
         'negative_local_styles': ['big drums', 'melody', 'major key']},
        {'section_name': 'Hush', 'duration_ms': 4200, 'lines': [],
         'positive_local_styles': ['near silence', 'single soft sustained low drone', 'one gentle reverse swell at the very end'],
         'negative_local_styles': ['drums', 'percussion', 'ticking', 'loud']},
        {'section_name': 'Lift', 'duration_ms': 17800, 'lines': [],
         'positive_local_styles': ['uplifting major key', 'confident rising string ostinato', 'driving pulse',
                                   'building energy and optimism', 'warm brass swells', 'momentum'],
         'negative_local_styles': ['dark', 'horror']},
        {'section_name': 'Full', 'duration_ms': 10000, 'lines': [],
         'positive_local_styles': ['full epic orchestra', 'big cinematic drums', 'heroic brass theme',
                                   'high intensity but controlled', 'propulsive'],
         'negative_local_styles': ['chaotic', 'aggressive distortion']},
        {'section_name': 'Recap hits', 'duration_ms': 9000, 'lines': [],
         'positive_local_styles': ['three huge orchestral hits spaced about one second apart',
                                   'sustained heroic chord after the hits', 'triumphant'],
         'negative_local_styles': ['busy rhythm']},
        {'section_name': 'Resolve', 'duration_ms': 4600, 'lines': [],
         'positive_local_styles': ['warm resolving final chord', 'one last big hit then a long reverb tail', 'confident ending'],
         'negative_local_styles': ['fade into new theme']},
    ],
}

if __name__ == '__main__':
    body = dict(composition_plan=PLAN, respect_sections_durations=True,
                output_format='mp3_44100_192')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/music', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=900))
    OUT.mkdir(parents=True, exist_ok=True)
    url = res['audio']['url'] if 'audio' in res else res['audio_file']['url']
    (OUT / 'score.mp3').write_bytes(urllib.request.urlopen(url, timeout=300).read())
    (OUT / 'score.plan.json').write_text(json.dumps(PLAN, indent=1))
    print('wrote public/audio/music/score.mp3')
