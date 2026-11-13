"""Animatic v3.0 sound: every effect is synthesized here (no generated clips, so nothing can contain a voice),
laid to the storyboard's sound line for each shot, then mixed with the score and the narrator.

  /opt/venv-audio/bin/python scripts/build_audio_v3.py

Writes public/audio/v3/{sfx,music,vo,mix}.wav plus public/audio/v3/elements/*.wav (each effect on its own,
for QC with scripts/audio_qc.py).

Storyboard V5 sound lines:
 01 Hard pulse score from frame one; outboards (flat out).        02 Radar sweep tone; muffled aircraft drone.
 03 Sensor servo whir; outboards under the score.                 04 Console tones; score drops to silence as the track goes dashed.
 05 One held tone in the silence, then the score starts to rebuild.  06 Water and wind; the score's pulse returns underneath.
 07 Engine spools to a full roar; the score kicks in on the lift.   08 Driving score; a data tone on each track update.
 09 Full engine roar, wind buffeting the mic.                      10 Engine drops to a hull-borne rumble; hull slap; distant radio.
 11 Score broadens and resolves; three hits on the three words.    12 Beat of silence, then a single engine rev to black.
"""
import json, os, pathlib, subprocess
import numpy as np
from scipy import signal
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/audio/v3'
SR = 48000
DUR = 60.0
rng = np.random.default_rng(20261113)

# ---- timeline (seconds), shared with the picture (src/v3/timeline.ts keeps the same numbers)
T = dict(
    radar_passes=[4.35, 5.10, 5.85, 6.60], radar_hook=6.05,
    mpa_breaks=12.8, track_dashed=13.4, music_out=(13.2, 14.3),
    fleet_on=16.0, score_rebuild=17.5, lift_kick=24.0,
    track_updates=[28.6, 30.1, 31.6, 33.1],
    settle=(42.6, 43.8), radio=[43.9, 45.2],
    vo=dict(vo1=23.3, vo2=42.0, vo3=52.0, vo4=57.1), hits=[52.0, 52.75, 53.72],
    rev=58.15,
)


# ---------------------------------------------------------------- dsp helpers
def n_(dur):
    return int(round(dur * SR))


def tt(dur):
    return np.arange(n_(dur)) / SR


def filt(x, kind, f, order=2):
    sos = signal.butter(order, f, btype=kind, fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def white(dur):
    return rng.standard_normal(n_(dur))


def colored(dur, power=1.0):
    """power 1 = pink, 2 = brown."""
    n = n_(dur)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    x = np.fft.irfft(spec / f ** (power / 2), n)
    return x / (np.abs(x).max() + 1e-9)


def harmonics(freq, amps, jitter=0.0):
    """freq: array of instantaneous frequency (Hz). amps: list of harmonic amplitudes (k = 1, 2, ...)."""
    if jitter:
        freq = freq * (1 + jitter * filt(rng.standard_normal(len(freq)), 'low', 12.0))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    return sum(a * np.sin(k * ph + 0.7 * k) for k, a in enumerate(amps, 1) if a)


def env(n, attack, release, curve=1.0):
    e = np.ones(n)
    a, r = min(n, n_(attack)), min(n, n_(release))
    if a:
        e[:a] = np.linspace(0, 1, a) ** curve
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** curve
    return e


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return np.clip((t - a) / (b - a), 0, 1)


def slow_random(dur, rate, depth):
    """Smooth random modulation around 1.0."""
    x = filt(rng.standard_normal(n_(dur)), 'low', rate)
    return 1 + depth * x / (np.abs(x).max() + 1e-9)


def rms_norm(x, db):
    r = np.sqrt(np.mean(x ** 2) + 1e-12)
    return x * (10 ** (db / 20) / r)


def peak_norm(x, db):
    return x * (10 ** (db / 20) / (np.abs(x).max() + 1e-9))


def reverb(x, decay=0.9, mix=0.25, pre=0.012):
    n = n_(decay * 2.2)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.9 / decay)
    ir = filt(ir, 'low', 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = signal.fftconvolve(np.concatenate([np.zeros(n_(pre)), x]), ir)[:len(x) + n]
    out = np.zeros(len(x) + n)
    out[:len(x)] += x * (1 - mix)
    out += wet[:len(out)] * mix
    return out


def pan(x, p):
    """p in [-1, 1] (constant power). p may be an array."""
    a = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


class Bus:
    def __init__(self):
        self.buf = np.zeros((n_(DUR), 2))
        self.elements = {}

    def add(self, name, x, t0, db, p=0.0, keep=True):
        """x mono; placed at t0 with peak-safe gain in dB relative to full scale RMS."""
        x = np.asarray(x, dtype=float)
        st = pan(x * 10 ** (db / 20), p) if x.ndim == 1 else x * 10 ** (db / 20)
        i0 = n_(t0)
        seg = st[:max(0, len(self.buf) - i0)]
        self.buf[i0:i0 + len(seg)] += seg
        if keep:
            self.elements.setdefault(name, []).append(x)


# ---------------------------------------------------------------- the effects
def engine_buzz(order_hz, n_harm=70, peak=420.0, width=1.5):
    """Combustion-engine drone: a dense comb of engine-order harmonics, each wandering in level on its own,
    under one broad spectral hump (deliberately no vowel-like resonances, so it never reads as a voice)."""
    n = len(order_hz)
    ph = 2 * np.pi * np.cumsum(order_hz) / SR
    out = np.zeros(n)
    for k in range(1, n_harm + 1):
        f = k * float(np.mean(order_hz))
        if f > 7000:
            break
        g = np.exp(-(np.log2(f / peak) / width) ** 2)
        if k % 4 == 0:
            g *= 2.2  # firing order stands out
        wander = filt(rng.standard_normal(n), 'low', 3.0)
        wander = 1 + 0.5 * wander / (np.abs(wander).max() + 1e-9)
        out += g * wander * np.sin(k * ph + rng.uniform(0, 6.28))
    return out


def outboards(dur, slam_hz=1.15, seed_phase=1.0, thumps=True):
    """Twin outboards flat out: hard engine drone whose revs flare as the hull slams, under water rush
    and hull slap."""
    t = tt(dur)
    slam = np.sin(2 * np.pi * slam_hz * t + seed_phase)
    airborne = smoothstep((slam - 0.55) / 0.45)  # props ventilate as the bow comes down: revs flare
    out = 0
    for det in (1.0, 1.023):
        order = 48.5 * det * (1 + 0.045 * airborne) * slow_random(dur, 0.8, 0.01)
        out = out + engine_buzz(order)
    rasp = filt(rng.standard_normal(len(t)), 'band', [60, 180])
    out = out * (1 + 0.35 * rasp / np.abs(rasp).max()) * slow_random(dur, 7.0, 0.12)
    out = filt(filt(out, 'high', 80), 'low', 6000)
    roar = filt(colored(dur, 0.9), 'band', [150, 3800]) * slow_random(dur, 14.0, 0.25)
    rush = filt(colored(dur, 0.7), 'band', [700, 7500]) * (0.55 + 0.45 * smoothstep((-slam + 0.2) / 0.8))
    thump_env = smoothstep((-slam - 0.72) / 0.28) ** 2
    thump = filt(colored(dur, 2.0), 'band', [40, 170]) * thump_env
    x = rms_norm(out, -22) + rms_norm(roar, -24) + rms_norm(rush, -23) + (rms_norm(thump, -25) * 1.4 if thumps else 0)
    return x * env(len(x), 0.02, 0.05)


def aircraft_drone(dur):
    """Muffled turboprop heard from inside: low beating blade-pass tone and cabin air."""
    t = tt(dur)
    x = 0
    for f0 in (84.0, 85.1):
        x = x + harmonics(np.full(len(t), f0) * slow_random(dur, 0.5, 0.002), [1.0, 0.55, 0.32, 0.14, 0.06])
    cabin = filt(colored(dur, 1.4), 'low', 700)
    return filt(rms_norm(x, -22) + rms_norm(cabin, -26), 'low', 650) * env(len(t), 0.04, 0.06)


def blip(freq, dur=0.05, decay=0.03):
    t = tt(dur)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t / decay) * env(len(t), 0.003, 0.004)


def tone(freq, dur, attack=0.01, release=0.08, harm=(1.0,)):
    t = tt(dur)
    return sum(a * np.sin(2 * np.pi * freq * k * t) for k, a in enumerate(harm, 1)) * env(len(t), attack, release)


def radar_sweep(dur=0.75):
    """One soft sweep: a quiet rising hum that resets, the 'sweep tone' of the display."""
    t = tt(dur)
    f = 300 + 160 * (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 1.5 * env(len(t), 0.02, 0.03)


def servo_whir(dur=0.95):
    """Gimbal slewing onto the contact: a small electric motor whine that runs up, overshoots and settles,
    then a soft mechanical stop."""
    t = tt(dur)
    k = 1 - np.exp(-t * 5.2) * (np.cos(t * 7.0) + 0.35 * np.sin(t * 7.0))
    speed = np.abs(np.gradient(k, 1 / SR))
    speed = filt(speed / speed.max(), 'low', 25)
    f = 1500 + 2300 * speed
    x = harmonics(f, [1.0, 0.35, 0.2, 0.1], jitter=0.004) * (0.08 + 0.92 * speed)
    x = x + 0.5 * filt(white(dur), 'band', [3000, 9000]) * speed
    stop = np.zeros(len(t))
    i = n_(0.86)
    c = 0.5 * filt(white(0.04), 'band', [1800, 7000]) * np.exp(-tt(0.04) / 0.005)
    stop[i:i + len(c)] += c[:len(stop) - i]
    return filt(filt(x, 'high', 900), 'low', 9000) * env(len(t), 0.01, 0.08) + stop


def held_tone(dur):
    """One held tone in the silence: a calm open fifth."""
    t = tt(dur)
    x = 0
    for f, a in ((146.83, 0.5), (293.66, 1.0), (440.0, 0.55), (587.33, 0.22)):
        for det in (-0.6, 0.0, 0.7):
            x = x + a * np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6.28))
    x = filt(x, 'low', 2200) * (1 + 0.05 * np.sin(2 * np.pi * 0.35 * t))
    return x * env(len(t), 0.9, 1.8, 1.5)


def water_and_wind(dur):
    """Open sea at night from a floating hull: small waves lapping and slapping, a light breeze. Stereo.
    Bright and splashy on purpose (low-heavy noise reads as rumble, not water)."""
    n = n_(dur)
    out = np.zeros((n, 2))
    t0 = 0.0
    while t0 < dur - 0.3:
        d = rng.uniform(0.5, 1.1)
        k = np.linspace(0, 1, n_(d))
        wash = filt(colored(d, 0.3), 'band', [rng.uniform(900, 1500), rng.uniform(5500, 8500)])
        wash *= np.sin(np.pi * k ** rng.uniform(0.45, 0.7)) ** 2
        # a few gurgly droplets inside each lap
        drops = np.zeros(len(k))
        for _ in range(rng.integers(3, 8)):
            i = rng.integers(0, max(1, len(k) - n_(0.06)))
            f0 = rng.uniform(900, 2600)
            dt = tt(0.05)
            blob = np.sin(2 * np.pi * (f0 + 900 * dt / 0.05) * dt) * np.exp(-dt / 0.012)
            drops[i:i + len(blob)] += blob[:len(drops) - i] * rng.uniform(0.2, 0.6)
        lap = wash + 0.5 * drops
        st = pan(lap * rng.uniform(0.45, 1.0), rng.uniform(-0.75, 0.75))
        i0 = n_(t0)
        seg = st[:n - i0]
        out[i0:i0 + len(seg)] += seg
        t0 += rng.uniform(0.3, 0.75)
    bed = filt(colored(dur, 0.6), 'band', [700, 6000]) * slow_random(dur, 0.8, 0.35)  # constant gentle wash
    wind = filt(colored(dur, 1.0), 'band', [350, 2200]) * slow_random(dur, 0.5, 0.5)
    bed_st = np.stack([bed, np.roll(bed, n_(0.007))], axis=1)
    wind_st = np.stack([wind, np.roll(wind, n_(0.013))], axis=1)
    out = rms_norm(out, -24) + rms_norm(bed_st, -31) + rms_norm(wind_st, -32)
    return out * env(n, 0.5, 0.6)[:, None]


def fan(freq, level, bright):
    """Marlin's ducted fan: blade-pass whine + air rush. freq/level/bright are arrays over time (bright 0..1)."""
    n = len(freq)
    dur = n / SR
    whine = harmonics(freq, [1.0, 0.6, 0.42, 0.3, 0.2, 0.14, 0.1, 0.07], jitter=0.003)
    whine = whine * (0.35 + 0.65 * bright)
    sub = harmonics(freq / 3.0, [0.8, 0.4, 0.2])
    air = colored(dur, 0.8)
    lo = filt(air, 'band', [180, 1400])
    hi = filt(air, 'band', [1400, 7000])
    rush = lo * (0.5 + 0.5 * (1 - bright)) + hi * bright * 1.3
    grit = filt(rng.standard_normal(n), 'band', [250, 5000])
    whine = whine * (1 + 0.5 * grit / np.abs(grit).max())  # blade-pass tone is rough, not a pure whistle
    x = rms_norm(whine, -27) + rms_norm(sub, -28) + rms_norm(rush, -19) * (0.35 + 0.65 * bright)
    return filt(x, 'low', 8500) * level * slow_random(dur, 4.0, 0.05)


def lift(dur=5.2):
    """07: spools up to a full roar, lifts, passes the waterline camera left to right and is gone. Returns stereo."""
    t = tt(dur)
    spool = smoothstep(ramp(t, 0.1, 2.1))
    freq = 55 * (480 / 55) ** spool
    # same motion as the Blender shot (blender/previz.py Shot07): x = X0 + a/2 (t - T0)^2, camera at x = 2.2, 9.6 m off the track
    X0, ACC, T0 = -12.0, 8.0, 0.45
    mx = X0 + 0.5 * ACC * np.maximum(0, t - T0) ** 2
    v_rad = np.tanh((t - 2.33) * 2.4)  # passes the camera at about 2.3 s: doppler drop, then it is away
    freq = freq * (1 - 0.055 * v_rad)
    dist = np.sqrt(9.6 ** 2 + (mx - 2.2) ** 2)
    level = np.clip(9.6 / dist, 0, 1) ** 0.85 * (0.25 + 0.75 * spool)
    x = fan(freq, level, bright=0.15 + 0.85 * spool)
    spray = filt(colored(dur, 0.6), 'band', [1800, 8000]) * smoothstep(ramp(t, 0.5, 1.2)) * (1 - smoothstep(ramp(t, 2.1, 3.3)))
    x = x + rms_norm(spray, -27) * np.clip(9.6 / dist, 0, 1)
    p = np.clip((mx - 2.2) / 14.0, -0.85, 0.85)
    return pan(x * env(len(t), 0.05, 0.9), p)


def run_roar(dur=6.0):
    """09: full engine roar with wind buffeting the mic; the sea builds."""
    t = tt(dur)
    build = 0.85 + 0.15 * t / dur
    x = fan(np.full(len(t), 470.0) * slow_random(dur, 0.7, 0.004), build, bright=np.full(len(t), 0.95))
    gust = np.abs(filt(rng.standard_normal(len(t)), 'low', 1.2))
    gust = (gust / gust.max()) ** 1.2
    flutter = 1 + 0.35 * filt(rng.standard_normal(len(t)), 'band', [18.0, 45.0]) / 0.2
    buffet = filt(colored(dur, 2.2), 'low', 230) * (0.55 + 0.6 * gust) * np.clip(flutter, 0.3, 1.8)
    hiss = filt(colored(dur, 0.5), 'band', [900, 5000]) * (0.5 + 0.5 * gust)
    water = filt(colored(dur, 1.0), 'band', [600, 6000]) * slow_random(dur, 3.0, 0.3)
    x = x + rms_norm(buffet, -17) + rms_norm(hiss, -31) + rms_norm(water, -30) * build
    return x * env(len(t), 0.03, 0.04)


def settle_rumble(dur=6.0):
    """10: faint fan under the sensor view, then the engine drops to a hull-borne rumble with hull slap."""
    t = tt(dur)
    drop = smoothstep(ramp(t, T['settle'][0] - 40.0, T['settle'][1] - 40.0))
    freq = 430 * (95 / 430) ** drop
    x = fan(freq, 0.55 * (1 - 0.45 * drop), bright=0.75 * (1 - drop) + 0.12)
    rumble = harmonics(np.full(len(t), 47.0) * slow_random(dur, 1.2, 0.01), [1.0, 0.7, 0.45, 0.3, 0.16, 0.1])
    rumble = filt(rumble * (1 + 0.3 * np.sin(2 * np.pi * 11.5 * t)), 'low', 420) * drop
    slap = np.zeros(len(t))
    ts = T['settle'][0] - 40.0 + 0.5
    while ts < dur - 0.5:
        d = 0.5
        s = filt(colored(d, 1.6), 'band', [70, 900]) * np.exp(-tt(d) / 0.09) + 0.5 * filt(colored(d, 0.8), 'band', [1200, 5000]) * np.exp(-tt(d) / 0.16)
        i = n_(ts)
        slap[i:i + len(s)] += s[:len(slap) - i] * rng.uniform(0.6, 1.0)
        ts += rng.uniform(0.75, 1.15)
    wash = filt(colored(dur, 1.0), 'band', [400, 4500]) * slow_random(dur, 1.5, 0.4) * drop
    x = x * (1 - 0.35 * drop) + rms_norm(rumble + 1e-9, -23) * drop + rms_norm(slap + 1e-9, -27) + rms_norm(wash + 1e-9, -31) * drop
    return x * env(len(t), 0.04, 0.25)


def radio_squelch(dur=0.42):
    """Distant radio: squelch opens on band-limited static and closes. No voice."""
    t = tt(dur)
    static = filt(white(dur), 'band', [450, 2800]) * (0.6 + 0.4 * slow_random(dur, 30, 0.6))
    static *= env(len(t), 0.004, 0.02)
    click = filt(white(0.02), 'band', [800, 3500]) * np.exp(-tt(0.02) / 0.004)
    x = static * 0.6
    x[:len(click)] += click
    x[-len(click):] += click[::-1] * 0.7
    return filt(x, 'low', 3200)


def impact(big=1.0):
    """Score hit: deep drop, body, and an airy tail."""
    d = 2.2
    t = tt(d)
    f = 34 + 62 * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    body = filt(colored(d, 1.8), 'band', [50, 380]) * np.exp(-t / 0.16)
    air = filt(colored(d, 0.4), 'band', [900, 4200]) * np.exp(-t / 0.5) * 0.25
    x = sub * 1.0 + peak_norm(body, -6) * 0.8 + peak_norm(air, -14)
    return reverb(x * env(len(t), 0.002, 0.3), decay=1.6, mix=0.28) * big


def engine_rev(dur=1.45):
    """12: a single engine rev, to black."""
    t = tt(dur)
    up = smoothstep(ramp(t, 0.0, 0.55))
    down = smoothstep(ramp(t, 0.65, 1.4))
    k = up * (1 - 0.85 * down)
    freq = 70 * (460 / 70) ** k
    x = fan(freq, 0.25 + 0.75 * k, bright=0.1 + 0.9 * k)
    return x * env(len(t), 0.03, 0.5, 1.6)


# ---------------------------------------------------------------- build
def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '2', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(float)


def build_sfx():
    b = Bus()
    # 01 outboards flat out (boat crosses from right of frame to centre as the camera slides aft)
    ob = outboards(4.05)
    b.add('01_outboards', ob, 0.0, -3.5, p=np.linspace(0.25, -0.1, len(ob)))
    # 02 radar sweep tone + muffled aircraft drone
    b.add('02_aircraft_drone', aircraft_drone(3.05), 4.0, -1.0)
    sweep_t0 = 4.0
    while sweep_t0 < 6.9:
        b.add('02_radar_sweep', radar_sweep(0.75), sweep_t0, -30.0, keep=sweep_t0 == 4.0)
        sweep_t0 += 0.75
    for tp in T['radar_passes']:
        b.add('02_radar_return', reverb(blip(1320, 0.07, 0.035), 0.35, 0.2), tp, -24.0, keep=tp == T['radar_passes'][0])
    hook = np.concatenate([blip(988, 0.06, 0.05), blip(1480, 0.09, 0.06)])
    b.add('02_hook', reverb(hook, 0.4, 0.2), T['radar_hook'], -21.0)
    # 03 sensor servo whir; outboards under the score (far below, filtered)
    b.add('03_servo', servo_whir(), 7.02, -24.0)
    far_ob = filt(filt(outboards(3.0, seed_phase=2.2, thumps=False), 'low', 1600), 'high', 140)  # heard from far off: no hull thumps
    b.add('03_outboards_under', far_ob, 7.0, -13.0)
    # 04 console tones
    b.add('04_tick', blip(1760, 0.03, 0.012), 10.12, -26.0)
    for tp, f in ((11.25, 880.0), (11.55, 880.0)):
        b.add('04_ring_ping', reverb(blip(f, 0.09, 0.05), 0.5, 0.25), tp, -25.0, keep=tp == 11.25)
    off = np.concatenate([tone(659.3, 0.16, 0.005, 0.05), tone(523.3, 0.26, 0.005, 0.16)])
    b.add('04_aircraft_off', reverb(off, 0.6, 0.25), T['mpa_breaks'] + 0.1, -23.0)
    lost = tone(311.1, 0.7, 0.01, 0.55, harm=(1.0, 0.3))
    b.add('04_track_dashed', reverb(lost, 0.9, 0.3), T['track_dashed'], -21.0)
    # 05 one held tone in the silence (+ a barely-there tick as each Marlin blinks on)
    b.add('05_held_tone', held_tone(5.2), T['fleet_on'] - 0.1, -25.0)
    for i in range(20):
        b.add('05_marker_tick', blip(2093 + 40 * (i % 5), 0.02, 0.008), T['fleet_on'] + 0.3 + ((i * 7) % 20) * 0.12, -38.0, p=rng.uniform(-0.6, 0.6), keep=i == 0)
    # 06 water and wind
    ww = water_and_wind(3.9)
    b.add('06_water_wind', ww, 19.85, -2.0)
    # 07 engine spools to a full roar, lifts and leaves
    b.add('07_lift', lift(), 22.95, 3.5)
    # 08 data tone on each track update
    dt = np.concatenate([blip(1568, 0.05, 0.03), blip(2093, 0.07, 0.04)])
    for tp in T['track_updates']:
        b.add('08_data_tone', reverb(dt, 0.35, 0.18), tp, -25.0, keep=tp == T['track_updates'][0])
    # 09 full engine roar, wind buffeting the mic
    b.add('09_run', run_roar(6.02), 34.0, -2.0)
    # 10 engine drops to a hull-borne rumble; hull slap; distant radio (squelch and static only)
    b.add('10_settle', settle_rumble(6.05), 40.0, -7.0)
    for tp in T['radio']:
        b.add('10_radio_squelch', radio_squelch(rng.uniform(0.3, 0.5)), tp, -31.0, p=0.35, keep=tp == T['radio'][0])
    # 11 fleet re-spaces: soft update ticks; three hits on the three words
    for tp in (47.5, 47.75, 48.0, 48.25, 48.5):
        b.add('11_respace_tick', blip(1568, 0.04, 0.02), tp, -31.0, keep=tp == 47.5)
    for i, tp in enumerate(T['hits']):
        b.add('11_hit', impact(1.0 if i < 2 else 1.12), tp - 0.01, -15.5, keep=i == 0)
    # 12 single engine rev to black
    b.add('12_engine_rev', engine_rev(), T['rev'], -1.0)
    return b


def gain_curve(points):
    """Piecewise-smooth gain automation from (time, dB) points."""
    t = np.arange(n_(DUR)) / SR
    ts, db = zip(*points)
    g = np.interp(t, ts, db)
    return (10 ** (g / 20))[:, None]


def duck(vo_times, vo_lens, depth_db, t_axis, extra=None):
    """Pull a stem down under each narrator line (extra = more dB for specific lines)."""
    d = np.zeros(len(t_axis))
    for k, s in vo_times.items():
        e = s + vo_lens[k]
        depth = depth_db + (extra or {}).get(k, 0.0)
        d = np.maximum(d, depth * smoothstep((t_axis - (s - 0.3)) / 0.3) * (1 - smoothstep((t_axis - e) / 0.5)))
    return (10 ** (-d / 20))[:, None]


def build_music(vo_lens):
    """Existing score cues (checked: no vocals), arranged to the storyboard's beats."""
    n = n_(DUR)
    out = np.zeros((n, 2))
    t = np.arange(n) / SR
    # Act 1: hard pulse from frame one; drops to silence as the track goes dashed
    a1 = load(ROOT / 'public/audio/music/score-v2.mp3')[n_(0.42):]
    seg = a1[:n_(T['music_out'][1] + 0.1)]
    g = (1 - smoothstep(ramp(t[:len(seg)], *T['music_out']))) * smoothstep(ramp(t[:len(seg)], 0.0, 0.03))
    out[:len(seg)] += seg * g[:, None] * 10 ** (-1.0 / 20)
    # Acts 2-3: one cue laid twice, three phrases (12 s) apart, so its kick lands on the lift and its
    # final phrase lands on "Cover." with the natural ending at the cut to the end card.
    cue = load(ROOT / 'public/audio/music/score-v2-act2.mp3')
    OFF_A = T['lift_kick'] - 16.5
    OFF_B = OFF_A + 12.0
    XF = 40.0

    def lay(offset, t0, t1, gain_fn):
        i0, i1 = n_(t0), n_(t1)
        src0 = n_(t0 - offset)
        seg = cue[src0:src0 + (i1 - i0)]
        tt_ = t[i0:i0 + len(seg)]
        out[i0:i0 + len(seg)] += seg * gain_fn(tt_)[:, None]

    def gA(x):
        rebuild = 10 ** (np.interp(x, [T['score_rebuild'], 20.0, 23.0, T['lift_kick'] - 0.05, T['lift_kick'], 33.7, 34.3], [-30, -13, -9, -8, -2.5, -2.5, -4.5]) / 20)
        return rebuild * smoothstep(ramp(x, T['score_rebuild'], T['score_rebuild'] + 0.8)) * np.cos(np.pi / 2 * smoothstep(ramp(x, XF - 0.2, XF + 0.2)))

    def gB(x):
        lvl = 10 ** (np.interp(x, [34.0, 34.3, 39.7, XF, 40.4, 45.6, 46.6, 51.6, 52.0, 55.8], [-4.5, -4.5, -4.5, -4.5, -7.0, -7.0, -3.0, -3.0, -2.0, -2.0]) / 20)
        return lvl * np.sin(np.pi / 2 * smoothstep(ramp(x, XF - 0.2, XF + 0.2))) * (1 - smoothstep(ramp(x, 55.86, 56.0)))
    lay(OFF_A, T['score_rebuild'], XF + 0.25, gA)
    lay(OFF_B, XF - 0.25, 56.02, gB)
    out *= duck(T['vo'], vo_lens, 6.0, t, extra=dict(vo3=3.5))  # the tagline has to sit clear of the biggest phrase
    return out


def build_vo():
    n = n_(DUR)
    out = np.zeros((n, 2))
    lens = {}
    for k, t0 in T['vo'].items():
        x = load(ROOT / f'public/audio/vo/{k}.mp3') * (10 ** (2.0 / 20) if k == 'vo3' else 1.0)
        lens[k] = len(x) / SR
        i0 = n_(t0)
        out[i0:i0 + len(x)] += x[:n - i0]
    return out, lens


def soft_limit(x, ceiling_db=-1.5):
    c = 10 ** (ceiling_db / 20)
    peak = np.abs(x).max(axis=1)
    win = n_(0.005)
    # simple look-ahead limiter: sliding max, smoothed
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    m = uniform_filter1d(maximum_filter1d(peak, size=win * 2), size=win)
    g = np.minimum(1.0, c / np.maximum(m, 1e-9))
    return x * g[:, None]


def main():
    (OUT / 'elements').mkdir(parents=True, exist_ok=True)
    sfx = build_sfx()
    for name, clips in sfx.elements.items():
        x = clips[0]
        sf.write(OUT / 'elements' / f'{name}.wav', peak_norm(x, -3.0), SR)
    vo, vo_lens = build_vo()
    music = build_music(vo_lens)
    t = np.arange(n_(DUR)) / SR
    # the end card opens on a beat of silence; nothing but the narrator's word and the rev after 56.0
    sfx_buf = sfx.buf * duck(T['vo'], vo_lens, 2.5, t)
    stems = dict(sfx=sfx_buf, music=music * 10 ** (-1.0 / 20), vo=vo * 10 ** (1.5 / 20))
    mix = soft_limit(sum(stems.values()))
    for k, v in stems.items():
        sf.write(OUT / f'{k}.wav', np.clip(v, -1, 1), SR, subtype='PCM_24')
    sf.write(OUT / 'mix_premaster.wav', mix, SR, subtype='PCM_24')
    # master: -14 LUFS integrated, -1.5 dBTP
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(OUT / 'mix_premaster.wav'), '-af',
                    'loudnorm=I=-14:TP=-1.5:LRA=13:linear=true', '-ar', str(SR), '-c:a', 'pcm_s24le', str(OUT / 'mix.wav')], check=True)
    # the edit uses a lossless FLAC of the master (the WAV stems are rebuildable and stay out of git)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(OUT / 'mix.wav'), '-c:a', 'flac', '-sample_fmt', 's16', str(OUT / 'mix.flac')], check=True)
    json.dump(dict(timeline=T, vo_lens=vo_lens), open(OUT / 'timeline.json', 'w'), indent=1)
    # per-second level report of each stem (dB RMS) so the balance can be read without listening
    print('sec   sfx  music    vo')
    for s in range(60):
        row = []
        for k in ('sfx', 'music', 'vo'):
            seg = stems[k][n_(s):n_(s + 1)]
            row.append(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
        print(f'{s:3d} ' + ' '.join(f'{v:6.1f}' if v > -90 else '   -- ' for v in row))


if __name__ == '__main__':
    main()
