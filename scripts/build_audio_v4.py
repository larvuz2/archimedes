"""Animatic v4.0 soundtrack: score + designed sound + narrator, built on the music's beat grid and mastered.

  /opt/venv-audio/bin/python scripts/build_audio_v4.py

Tone target = the client's reference film (docs/reference-analysis.md): wall-to-wall, dark to bright, hits on
the cuts, a drop-out before the last act, biggest hit on the end card. Everything lands on beats:
    t(k) = T0 + k * 60/104      (k = beat number; bars are 4 beats; T0 = first beat of the score)

Sources (all checked with scripts/audio_qc.py): public/audio/v4/music.mp3 (ElevenLabs Music),
public/audio/v4/sfx_src/*.mp3 (ElevenLabs Sound Effects), public/audio/v4/vo/*.wav (ElevenLabs v3, voice Brian),
plus synthesized elements from scripts/build_audio_v3.py. Mastering uses Spotify's open-source Pedalboard.
Writes public/audio/v4/{mix.flac, music.wav, sfx.wav, vo.wav, timeline.json}.
"""
import json, pathlib, subprocess, sys
import numpy as np
import soundfile as sf
from pedalboard import Pedalboard, Compressor, Limiter, HighpassFilter, LowpassFilter, PeakFilter, HighShelfFilter, Reverb, Gain

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_audio_v3 as A  # dsp helpers and a few synthesized effects

ROOT = pathlib.Path(__file__).resolve().parent.parent
V4 = ROOT / 'public/audio/v4'
SR = A.SR
DUR = 60.0
BEAT = 60 / 104
T0 = 0.345
rng = np.random.default_rng(4)


def t(k):
    return T0 + k * BEAT


# ---- the edit's anchors (beats). src/v4/timeline.ts uses the same numbers.
K = dict(hook=0, waits=8, hit2=12, pre=20, detect=24, isolate=36, breakdown=56, surveil=60, finale=80, w1=84, w2=88, w3=92, end=96)
VO = dict(v01=1.00, v02=5.25, v03=8.10, v04=9.90, v05=14.75, v06=21.75, v07=24.45, v08=30.55, v09=35.70, v10=38.50,
          v11=t(K['w1']) - 0.04, v12=t(K['w2']) - 0.04, v13=t(K['w3']) - 0.04, v14=t(K['end']) + 0.62)

n_ = A.n_
smoothstep, ramp = A.smoothstep, A.ramp


def src(name, gain_db=0.0):
    x = A.load(V4 / 'sfx_src' / f'{name}.mp3')
    return x * 10 ** (gain_db / 20)


def fade(x, a=0.01, r=0.05):
    n = len(x)
    e = np.ones(n)
    na, nr = min(n, n_(a)), min(n, n_(r))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return x * (e[:, None] if x.ndim == 2 else e)


def loop(x, dur, xf=0.6):
    """Repeat a clip with crossfades to fill dur seconds."""
    n, nx = n_(dur), n_(xf)
    out = np.zeros((n, 2))
    pos = 0
    seg = fade(x, xf, xf)
    step = len(x) - nx
    while pos < n:
        m = min(len(seg), n - pos)
        out[pos:pos + m] += seg[:m]
        pos += step
    return out


def speed(x, f):
    """Play faster/slower (pitch follows)."""
    idx = np.arange(0, len(x) - 1, f)
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1)


def norm(x, db, mode='rms'):
    if mode == 'peak':
        return x * (10 ** (db / 20) / (np.abs(x).max() + 1e-9))
    return x * (10 ** (db / 20) / (np.sqrt(np.mean(x ** 2)) + 1e-9))


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


def lp(x, hz):
    """Low-pass a stereo clip (takes the hiss off the air layers so nothing reads as shrill)."""
    return np.stack([A.filt(x[:, c], 'low', hz) for c in range(2)], axis=1)


def panned(x, p):
    m = x.mean(axis=1) if x.ndim == 2 else x
    return A.pan(m, p)


class Bus:
    def __init__(self):
        self.buf = np.zeros((n_(DUR), 2))

    def add(self, x, at, db=0.0, end_at=None):
        """Place a stereo clip. end_at=True aligns the END of the clip to `at` (for risers / reverse swells)."""
        x = st(np.asarray(x, dtype=float)) * 10 ** (db / 20)
        i0 = n_(at) - (len(x) if end_at else 0)
        if i0 < 0:
            x, i0 = x[-i0:], 0
        seg = x[:max(0, len(self.buf) - i0)]
        self.buf[i0:i0 + len(seg)] += seg


# ---------------------------------------------------------------- synthesized trailer elements
def sub_boom(dur=2.4, f0=38.0, drop=70.0, decay=0.55):
    tt = A.tt(dur)
    f = f0 + drop * np.exp(-tt / 0.07)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / decay)
    click = A.filt(A.white(0.03), 'band', [900, 5000]) * np.exp(-A.tt(0.03) / 0.004)
    x[:len(click)] += 0.35 * click
    return x * A.env(len(tt), 0.001, 0.3)


def heartbeat():
    """Lub-dub: the predator's pulse while it waits."""
    out = np.zeros(n_(0.62))
    for at, g, f in ((0.0, 1.0, 46.0), (0.21, 0.72, 52.0)):
        tt = A.tt(0.3)
        hit = np.sin(2 * np.pi * (f + 30 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.075) * g
        i = n_(at)
        out[i:i + len(hit)] += hit[:len(out) - i]
    return out


def swish(dur=0.42, lo=400.0, hi=4200.0):
    """Short air whoosh for a cut: band of noise sweeping up then down."""
    tt = A.tt(dur)
    x = A.white(dur)
    k = np.sin(np.pi * tt / dur) ** 1.5
    out = np.zeros(len(tt))
    for i in range(0, len(tt), 512):  # crude time-varying band-pass
        c = lo * (hi / lo) ** k[min(i + 256, len(tt) - 1)]
        seg = x[max(0, i - 2048):i + 512 + 2048]
        y = A.filt(seg, 'band', [c * 0.6, min(c * 1.7, SR / 2 - 100)])
        s0 = i - max(0, i - 2048)
        out[i:i + 512] = y[s0:s0 + len(out[i:i + 512])]
    return out * k


def ui_ping(freq, dur=0.16):
    return A.reverb(A.blip(freq, dur, 0.05), 0.45, 0.22)


def sensor_hum(dur):
    tt = A.tt(dur)
    x = sum(a * np.sin(2 * np.pi * f * tt + p) for f, a, p in ((180, 1.0, 0), (181.3, 0.8, 1), (360.5, 0.35, 2), (2400, 0.05, 0)))
    return A.filt(x, 'low', 3000) * A.env(len(tt), 0.2, 0.3) * (1 + 0.1 * np.sin(2 * np.pi * 7 * tt))


# ---------------------------------------------------------------- build
def build_sfx():
    b = Bus()
    impact, braam, whoosh, riser, suck, sonar = (src(n) for n in ('impact', 'braam', 'whoosh', 'riser', 'suck', 'sonar'))
    impact, braam = norm(impact, -3, 'peak'), norm(braam, -4, 'peak')
    whoosh, riser, suck, sonar = norm(lp(whoosh, 6000), -6, 'peak'), norm(riser, -6, 'peak'), norm(suck, -6, 'peak'), norm(sonar, -6, 'peak')
    boom = st(norm(sub_boom(), -3, 'peak'))

    def hit(k, db=0.0, with_braam=True, braam_db=-4.0, boom_db=-2.0):
        db -= 4.0
        b.add(impact, t(k) - 0.012, db)
        b.add(boom, t(k) - 0.004, db + boom_db)
        if with_braam:
            b.add(fade(braam, 0.004, 0.9), t(k) - 0.01, db + braam_db)

    def cut_whoosh(k, db=-12.0, p=0.0, rate=1.0):
        w = speed(whoosh, rate)
        b.add(panned(w, p) * 1.3, t(k) - 0.16 * (1 / rate), db)
        b.add(panned(st(swish()), -p), t(k) - 0.2, db - 5)

    # ---- HOOK (k0-8): the go-fast, loud and close, then it is gone
    gofast = norm(src('gofast'), -15)
    g = fade(loop(gofast, t(K['waits']) + 0.05, 0.5), 0.35, 0.07)
    b.add(g, 0.0, -1.0)
    hit(0, -4.0, with_braam=False)
    b.add(fade(suck, 0.02, 0.02), t(K['waits']), -9.0, end_at=True)
    # ---- MARLIN WAITS (k8-20): near silence, sea, a slow pulse
    sea = norm(loop(src('ocean_night'), t(K['detect']) - t(K['waits']) + 0.5, 1.2), -23)
    water = norm(A.water_and_wind(t(K['detect']) - t(K['waits']) + 0.5), -26)
    b.add(fade(sea + water[:len(sea)], 0.25, 0.5), t(K['waits']), 0.0)
    hb = st(norm(heartbeat(), -3, 'peak'))
    for i, k in enumerate(range(K['waits'], K['detect'] - 1, 2)):
        b.add(hb, t(k), -11.0 + 0.9 * i)
    hit(K['hit2'], -9.0, with_braam=False, boom_db=0.0)
    # ---- PRE-DETECT (k20-24): the sensor sweeps and stops; riser into the slam
    b.add(st(norm(A.servo_whir(1.05), -3, 'peak')), t(K['pre']) + 0.02, -17.0)
    b.add(fade(src('underwater')[:n_(0.9)], 0.02, 0.3), t(22), -14.0)
    b.add(st(ui_ping(1568)), t(22), -20.0)
    b.add(fade(riser, 0.02, 0.01), t(K['detect']), -8.0, end_at=True)
    # ---- DETECT (k24-36)
    hit(K['detect'], -1.0)
    b.add(fade(sonar, 0.002, 0.4), t(K['detect']) + 0.03, -6.0)
    for i, k in enumerate((26, 26.5, 27)):  # the three nearest Marlins light up
        b.add(panned(st(ui_ping(1175 * 1.26 ** i)), (-0.5, 0.1, 0.55)[i]), t(k), -17.0)
    b.add(fade(sonar, 0.002, 0.4), t(26), -13.0)
    fan = norm(src('fan_spool'), -14)
    b.add(fade(fan, 0.05, 0.25), t(28) - 0.15, -2.0)
    for i, k in enumerate((30, 30.5, 31)):  # three vectors draw
        b.add(panned(st(swish(0.36)), (-0.6, 0.0, 0.6)[i]), t(k) - 0.05, -15.0)
        b.add(st(A.blip(1568 + 260 * i, 0.05, 0.02)), t(k), -24.0)
    run = norm(lp(src('run'), 5500), -17)
    lift = fade(loop(run, t(K['isolate']) - t(32) + 0.1, 0.5), 0.6, 0.08)
    lift *= np.linspace(0.45, 1.25, len(lift))[:, None]
    b.add(lift, t(32), -3.0)
    b.add(panned(norm(src('passby'), -8, 'peak'), np.linspace(-0.8, 0.8, len(src('passby')))), t(34) - 0.2, -6.0)
    cut_whoosh(33, -14, -0.4)
    cut_whoosh(35, -12, 0.4, 1.15)
    b.add(fade(suck[-n_(0.9):], 0.02, 0.01), t(K['isolate']), -9.0, end_at=True)
    # ---- ISOLATE (k36-56): full power
    hit(K['isolate'], 0.0)
    bed = loop(run, t(K['breakdown']) - t(K['isolate']), 0.6)
    env_ = np.ones(len(bed))
    tb = np.arange(len(bed)) / SR + t(K['isolate'])
    for a_, b_ in ((42, 43), (48, 50), (54, 56)):  # map cuts: the engine bed drops away
        env_ *= 1 - 0.85 * smoothstep((tb - (t(a_) - 0.04)) / 0.05) * (1 - smoothstep((tb - t(b_) + 0.03) / 0.05))
    b.add(fade(bed * env_[:, None], 0.03, 0.06), t(K['isolate']), -4.5)
    for i, k in enumerate((38, 39, 40, 43, 44, 46, 47, 50, 51, 52)):
        cut_whoosh(k, -13.0 + (i % 3), (-0.55, 0.55, 0.0)[i % 3], (1.0, 1.12, 0.9)[i % 3])
    for k in (42, 48):
        b.add(fade(sonar, 0.002, 0.4), t(k), -13.0)
        b.add(st(A.blip(2093, 0.04, 0.015)), t(k) + 0.14, -24.0)
    b.add(panned(norm(src('passby'), -8, 'peak'), np.linspace(0.7, -0.7, len(src('passby')))), t(52) - 0.25, -8.0)
    hit(54, -5.0, braam_db=-7.0)
    # ---- BREAKDOWN (k56-60): the score drops out; we are inside the sensor
    b.add(fade(suck, 0.02, 0.01), t(K['breakdown']), -7.0, end_at=True)
    b.add(fade(norm(src('underwater'), -20), 0.05, 0.4), t(K['breakdown']), 0.0)
    b.add(st(sensor_hum(t(K['surveil']) - t(K['breakdown']))), t(K['breakdown']), -31.0)
    for k in (57, 58.5):
        b.add(hb, t(k), -9.0)
    b.add(fade(riser, 0.02, 0.01), t(K['surveil']), -7.0, end_at=True)
    # ---- SURVEIL (k60-80): heavy, controlled
    hit(K['surveil'], 0.0)
    b.add(fade(norm(src('splash'), -6, 'peak'), 0.002, 0.3), t(K['surveil']) + 0.02, -7.0)
    idle = norm(src('idle'), -22)
    b.add(fade(loop(idle, t(K['finale']) - t(K['surveil']), 0.8), 0.4, 0.3), t(K['surveil']), -2.0)
    for k in (66, 74):  # partner track on the display
        b.add(fade(sonar, 0.002, 0.4), t(k), -10.0)
    b.add(st(ui_ping(1760)), t(62), -19.0)  # LIVE
    cut_whoosh(64, -15, 0.3)
    cut_whoosh(68, -15, -0.3)
    hit(72, -8.0, with_braam=False)
    hit(76, -5.0, braam_db=-8.0)
    for i, k in enumerate((78, 78.5, 79, 79.5)):  # stutter into the finale
        cut_whoosh(k, -13.0 + i, (-0.6, 0.6)[i % 2], 0.84 + 0.05 * i)
    b.add(fade(riser[-n_(1.2):], 0.05, 0.01), t(K['finale']), -9.0, end_at=True)
    # ---- FINALE (k80-96): three words, three hits, then the name
    hit(K['finale'], -2.0)
    for k in (K['w1'], K['w2'], K['w3']):
        b.add(panned(speed(whoosh, 0.85), 0.0), t(k) - 0.3, -11.0)
        hit(k, +1.0, braam_db=-3.0)
    b.add(fade(suck, 0.02, 0.005), t(K['end']) - 0.05, -5.0, end_at=True)
    b.add(fade(riser, 0.02, 0.005), t(K['end']) - 0.05, -9.0, end_at=True)
    # ---- END CARD (k96): the biggest hit, then it rings out. No engine.
    hit(K['end'], +2.5, braam_db=-2.0, boom_db=0.0)
    b.add(st(norm(sub_boom(3.6, 32.0, 60.0, 1.1), -3, 'peak')), t(K['end']), -2.0)
    b.add(fade(norm(loop(src('ocean_night'), 4.2, 1.0), -31), 0.6, 2.2), t(K['end']) + 0.4, 0.0)
    return b.buf


TARGET_LUFS = -14.0
CEILING = 10 ** (-3.0 / 20)


def loudness(path):
    """Integrated loudness, range, true peak and the short-term curve (every 3 s) from ffmpeg's EBU R128 meter."""
    import re
    err = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summary = err[err.rindex('Summary:'):]
    g = lambda key: float(re.search(key + r':\s*(-?[\d.]+)', summary).group(1))
    st = {int(float(a)): float(b) for a, b in re.findall(r't:\s*([\d.]+)\s+TARGET.*?S:\s*(-?[\d.]+)', err)}
    return g('I'), g('LRA'), g('Peak'), [st.get(i, -70.0) for i in range(3, 60, 3)]


def duck(vo_lens, depth_db, t_axis, lead=0.18, tail=0.35):
    d = np.zeros(len(t_axis))
    for k, s in VO.items():
        e = s + vo_lens[k]
        d = np.maximum(d, depth_db * smoothstep((t_axis - (s - lead)) / lead) * (1 - smoothstep((t_axis - e) / tail)))
    return (10 ** (-d / 20))[:, None]


def build_vo():
    chain = Pedalboard([HighpassFilter(70), PeakFilter(160, gain_db=1.5, q=0.9), PeakFilter(3200, gain_db=2.5, q=0.8),
                        HighShelfFilter(8000, gain_db=1.5), Compressor(threshold_db=-20, ratio=3.5, attack_ms=4, release_ms=120), Gain(4.0)])
    verb = Pedalboard([Reverb(room_size=0.22, damping=0.6, wet_level=0.07, dry_level=1.0, width=0.9)])
    out = np.zeros((n_(DUR), 2))
    lens = {}
    for k, at in VO.items():
        x, sr = sf.read(V4 / 'vo' / f'{k}.wav', dtype='float32')
        assert sr == SR
        x = norm(x, -20.0)
        if k in ('v11', 'v12', 'v13', 'v14'):  # the words that carry the film sit a little harder
            x = x * 10 ** (1.5 / 20)
        if k in ('v06', 'v07', 'v08', 'v09', 'v10'):  # lines spoken over the score at full power
            x = x * 10 ** (2.0 / 20)
        y = chain(x[None, :], SR)
        y = verb(np.repeat(y, 2, axis=0), SR).T
        lens[k] = len(x) / SR
        i0 = n_(at)
        out[i0:i0 + len(y)] += y[:len(out) - i0]
    return out, lens


def build_music(vo_lens):
    m = A.load(V4 / 'music.mp3')[:n_(DUR)]
    m = np.pad(m, ((0, n_(DUR) - len(m)), (0, 0)))
    tt = np.arange(len(m)) / SR
    # level ride: a touch under in the quiet opening, full from the detect slam, pushed for the finale
    ride = np.interp(tt, [0, t(K['waits']), t(K['detect']) - 0.1, t(K['detect']), t(K['isolate']), t(K['finale']), t(K['end']), 60],
                     [-1.0, -2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 1.5])
    return m * (10 ** (ride / 20))[:, None] * duck(vo_lens, 6.0, tt)


def master(music, sfx, vo):
    """Pedalboard master: an automation ride that gives the film its arc, light glue compression, then a static gain
    into a brick-wall limiter. The gain is found by measurement so the film lands at the reference's loudness
    (-14 LUFS) WITHOUT levelling: the opening stays under the detect slam and the build to the end card survives
    (ffmpeg loudnorm's dynamic mode would flatten it)."""
    tt = np.arange(n_(DUR)) / SR
    arc = np.interp(tt, [0, t(K['detect']) - 0.3, t(K['detect']) - 0.02, t(K['breakdown']) - 0.05, t(K['breakdown']) + 0.15, t(K['surveil']) - 0.3,
                         t(K['surveil']) - 0.02, t(K['finale']), t(K['w1']), 60],
                    [-5.0, -3.5, 0.0, 0.0, -3.0, -2.5, 0.0, 0.7, 1.6, 1.6])
    mix = ((music + sfx + vo) * 10 ** (-6.0 / 20) * (10 ** (arc / 20))[:, None]).astype(np.float32)
    glue = Pedalboard([HighpassFilter(28), Compressor(threshold_db=-16, ratio=1.6, attack_ms=30, release_ms=250)])
    limiter = Pedalboard([Limiter(threshold_db=-2.6, release_ms=90)])
    pre = glue(mix.T, SR)
    gain_db = 0.0
    for _ in range(5):
        out = limiter(pre * 10 ** (gain_db / 20), SR).T
        out = np.clip(out, -CEILING, CEILING)  # the limiter lets a few hundred samples overshoot; hold them under the ceiling
        sf.write(V4 / 'mix_premaster.wav', out, SR, subtype='PCM_24')
        i_lufs, lra, peak, curve = loudness(V4 / 'mix_premaster.wav')
        if abs(TARGET_LUFS - i_lufs) < 0.15:
            break
        gain_db += TARGET_LUFS - i_lufs
    out[-n_(0.25):] *= np.linspace(1, 0, n_(0.25))[:, None]
    sf.write(V4 / 'mix_premaster.wav', out, SR, subtype='PCM_24')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V4 / 'mix_premaster.wav'), '-ar', str(SR), '-c:a', 'flac', '-sample_fmt', 's16', str(V4 / 'mix.flac')], check=True)
    i_lufs, lra, peak, curve = loudness(V4 / 'mix.flac')
    print(f'master gain {gain_db:+.1f} dB -> {i_lufs:.1f} LUFS, LRA {lra:.1f} LU, true peak {peak:.1f} dBFS')
    print('short-term loudness every 3 s:', ' '.join(f'{v:.0f}' for v in curve))


def main():
    if '--master-only' in sys.argv:  # re-master from the stems on disk
        music, sfx, vo = (sf.read(V4 / f'{n}.wav', dtype='float64')[0] for n in ('music', 'sfx', 'vo'))
        return master(music, sfx, vo)
    vo, vo_lens = build_vo()
    music = build_music(vo_lens) * 10 ** (-2.0 / 20)
    tt = np.arange(n_(DUR)) / SR
    sfx = build_sfx() * duck(vo_lens, 6.5, tt)
    for name, x in (('music', music), ('sfx', sfx), ('vo', vo)):
        sf.write(V4 / f'{name}.wav', x, SR, subtype='FLOAT')
    json.dump(dict(beat=BEAT, t0=T0, K=K, vo=VO, vo_lens=vo_lens), open(V4 / 'timeline.json', 'w'), indent=1)
    print('sec   sfx  music    vo')
    for s in range(60):
        row = [20 * np.log10(np.sqrt(np.mean(x[n_(s):n_(s + 1)] ** 2)) + 1e-9) for x in (sfx, music, vo)]
        print(f'{s:3d} ' + ' '.join(f'{v:6.1f}' if v > -90 else '   -- ' for v in row))
    master(music, sfx, vo)


if __name__ == '__main__':
    main()
