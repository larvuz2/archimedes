"""Sound effects through fal.ai (ElevenLabs Sound Effects v2): real engine, water and console audio
per Storyboard V5. Writes public/audio/sfx/<id>.mp3. Needs FAL_KEY.

  python3 scripts/generate_sfx.py [--only s06 s08]
"""
import argparse, json, os, pathlib, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/sfx'
SFX = {
    's01_outboards': (5.0, 'Twin high-powered outboard engines screaming at full throttle on a small speedboat at night, hull slamming on waves, spray hissing, close perspective'),
    's02_radar': (4.0, 'Airborne maritime search radar sweep tone with a soft electronic ping, under a muffled turboprop aircraft cabin drone'),
    's03_servo': (3.0, 'Gimbal camera servo whir, small precise electronic motor slewing quickly then settling with a soft click'),
    's04_console': (6.0, 'Soft operations console interface tones, quiet data beeps and a low electronic hum, calm and professional'),
    's05_ocean': (7.0, 'Open ocean at night, long gentle swell lapping against a small floating hull, light wind, distant and calm'),
    's06_spool': (6.0, 'Electric ducted fan spooling up from idle to a full powerful roar as a fast craft accelerates and lifts out of the water, rushing water and spray'),
    's07_datatone': (1.0, 'Single short clean digital data update tone, subtle'),
    's08_roar': (7.0, 'High-speed hydrofoil craft running at full speed at night, powerful ducted fan roar, strong wind buffeting the microphone, water hiss'),
    's09_rumble': (7.0, 'Small vessel slowing to a low idling engine rumble, hull slapping on waves, faint unintelligible radio chatter in the distance'),
    's11_heldtone': (5.0, 'Single soft sustained cinematic synth tone, warm and hopeful, steady pitch, no rhythm, gentle swell in and slow tail'),
    's12_hit': (2.5, 'One huge cinematic orchestral impact hit with deep boom and short reverb tail, trailer style'),
    's10_rev': (3.0, 'Single powerful ducted fan engine rev that cuts off abruptly to silence'),
}


def gen(sid):
    dur, text = SFX[sid]
    body = dict(text=text, duration_seconds=dur, prompt_influence=0.5, output_format='mp3_44100_128')
    req = urllib.request.Request('https://fal.run/fal-ai/elevenlabs/sound-effects/v2', data=json.dumps(body).encode(),
                                 headers={'Authorization': f"Key {os.environ['FAL_KEY']}", 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=300))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{sid}.mp3').write_bytes(urllib.request.urlopen(res['audio']['url'], timeout=300).read())
    return sid


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--only', nargs='*'); a = ap.parse_args()
    with ThreadPoolExecutor(5) as ex:
        for s in ex.map(gen, a.only or list(SFX)):
            print('wrote', s)
