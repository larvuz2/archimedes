"""Ask an audio-understanding model (fal-ai/audio-understanding) what is in a clip.
Second-opinion QA for generated audio, since nobody listens during generation.
  python3 scripts/audio_describe.py public/audio/sfx/s01_outboards.mp3 [more files...]
"""
import base64, json, os, sys, urllib.request

PROMPT = ("Describe exactly what you hear in this audio clip, in order. Then answer on separate lines: "
          "HUMAN_VOICE: yes/no (any speech, shouting, screaming, singing, crying or vocal sounds, even brief). "
          "SCREAM: yes/no. MUSIC: yes/no. Then one line: MAIN_SOUNDS: comma-separated list.")


def describe(path, prompt=PROMPT):
    mime = 'audio/mpeg' if path.endswith('.mp3') else 'audio/wav'
    uri = f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()
    req = urllib.request.Request('https://fal.run/fal-ai/audio-understanding',
                                 data=json.dumps(dict(audio_url=uri, prompt=prompt, detailed_analysis=True)).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=300))['output']


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(f'=== {p}')
        try:
            print(describe(p))
        except urllib.error.HTTPError as e:
            print('ERROR', e.code, e.read().decode()[:400])
