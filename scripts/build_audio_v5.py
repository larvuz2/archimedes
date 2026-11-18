"""Animatic v5.0 soundtrack (Storyboard V7): score + designed sound + narrator on the score's beat grid, mastered.

  /opt/venv-audio/bin/python scripts/build_audio_v5.py            # build stems and master
  /opt/venv-audio/bin/python scripts/build_audio_v5.py --master-only
  /opt/venv-audio/bin/python scripts/build_audio_v5.py --vo public/audio/v5/vo_deep/Brian --tag deep   # option B -> mix_deep.flac

The score (public/audio/v5/music.mp3, ElevenLabs Music) runs at exactly 104 BPM with its first beat at 0.055 s:
    t(k) = 0.055 + k * 60/104          (src/v5/timeline.ts uses the same grid)
It plays the whole way through; the storyboard's shape is made here: it tightens under the radar, sinks with a tape-stop into
silence as the track goes dashed, a held tone, the kick on the lift, a build into STOP, a tape-stop as the engines die
("then only water"), relief, three hits on the three words, and a beat of silence before the end card.
Narration: ElevenLabs v3 "Callum", picked by scripts/pick_vo_v5.py. Effects: public/audio/v4/sfx_src, public/audio/v5/sfx_src
and synthesized elements; every source passed scripts/audio_qc.py. Mastering: Spotify's open-source Pedalboard.
"""
import json, pathlib, subprocess, sys
import numpy as np
import soundfile as sf
from pedalboard import Pedalboard, Compressor, Limiter, HighpassFilter, LowpassFilter, PeakFilter, HighShelfFilter, Reverb, Gain

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_audio_v3 as A  # synth helpers
import build_audio_v4 as B4  # v4 helpers (fades, loops, booms, swishes, pings, loudness)

ROOT = pathlib.Path(__file__).resolve().parent.parent
V5 = ROOT / 'public/audio/v5'
V4 = ROOT / 'public/audio/v4'
SR = A.SR
DUR = 60.0
BEAT = 60 / 104
T0 = 0.055
n_, smoothstep = A.n_, A.smoothstep
fade, loop, speed, norm, st, lp, panned = B4.fade, B4.loop, B4.speed, B4.norm, B4.st, B4.lp, B4.panned
sub_boom, swish, ui_ping, heartbeat = B4.sub_boom, B4.swish, B4.ui_ping, B4.heartbeat


def t(k):
    return T0 + k * BEAT


# ---- story timing (mirrors src/v5/timeline.ts)
RADAR_PASSES = [4.6, 5.35, 6.1, 6.85, 7.6, 8.35]
CUE, HOOK, DETECTED, DESIGNATED = 5.0, 6.25, 6.45, 7.35
MPA_BREAKS, TRACK_DASHED = 11.2, 11.9
FLEET_ON, TASK, INTERCEPT = t(24.5), t(28), t(29)
UPDATES = [t(39), t(40.5), t(42), t(43.5)]
IR_PULL = t(45) + 1.5
AUTHORIZED, PLAN = t(54) + 0.15, t(55)
NET_FIRE = t(66) + 0.65
FOUL = t(72) + 1.379 / 0.87
RESPACE = t(89)
WORDS = [t(90), t(92), t(94)]
END_CUT, LOGO = t(97), t(98)
SINK = (t(16), t(23))  # the score sinks to silence (03, as the track goes dashed)
KICK = t(32)  # the lift
BUILD = (t(52), t(60))  # stop authorized: the score builds into STOP
STOP = t(60)
DIE = (FOUL + 0.08, FOUL + 0.78)  # the engines choke and the score stops with them
RETURN = (t(80), t(88))  # hold: the score comes back up
VO = dict(l1ab=t(32) + 0.12, l1c=t(38) + 0.1, l2=t(47), l3=t(60) + 0.3, l4=t(80) + 0.45, l5a=t(90), l5b=t(92), l5c=t(94), l6=t(98) + 0.45)


class Bus:
    def __init__(self):
        self.buf = np.zeros((n_(DUR), 2))

    def add(self, x, at, db=0.0, end_at=False):
        x = st(np.asarray(x, dtype=float)) * 10 ** (db / 20)
        i0 = n_(at) - (len(x) if end_at else 0)
        if i0 < 0:
            x, i0 = x[-i0:], 0
        seg = x[:max(0, len(self.buf) - i0)]
        self.buf[i0:i0 + len(seg)] += seg


def src4(name):
    return A.load(V4 / 'sfx_src' / f'{name}.mp3')


def src5(name):
    return A.load(V5 / 'sfx_src' / f'{name}.mp3')


def tape_stop(x, a, b):
    """Slow the audio from a to b down to a standstill (pitch and speed fall together), silence after."""
    i0, i1 = n_(a), n_(b)
    L = i1 - i0
    u = np.arange(L) / L
    pos = i0 + L * (u - u * u / 2)  # speed 1 -> 0
    out = x.copy()
    for c in range(2):
        out[i0:i1, c] = np.interp(pos, np.arange(len(x)), x[:, c]) * (1 - smoothstep((u - 0.75) / 0.25))
    out[i1:] = 0
    return out


def sweep_filter(x, a, b, f0, f1, kind='low', steps=48):
    """Time-varying filter over [a, b]: cutoff moves exponentially from f0 to f1 (block-wise, crossfaded)."""
    out = x.copy()
    edges = np.linspace(n_(a), n_(b), steps + 1).astype(int)
    for j in range(steps):
        s0, s1 = edges[j], edges[j + 1]
        f = f0 * (f1 / f0) ** ((j + 0.5) / steps)
        pad = 4096
        lo, hi = max(0, s0 - pad), min(len(x), s1 + pad)
        seg = np.stack([A.filt(x[lo:hi, c], kind, min(f, SR / 2 - 200), order=2) for c in range(2)], axis=1)
        out[s0:s1] = seg[s0 - lo:s0 - lo + (s1 - s0)]
    return out


def net_splashes(n=7, span=1.0, seed=3):
    """The net's floats landing along each leg: a quick run of short splashes, centre out to both sides (synthesized; the
    generated clip read as a 'gobble' in the mix)."""
    r = np.random.default_rng(seed)
    out = np.zeros((n_(span + 0.4), 2))
    for i in range(n):
        at = span * (i / (n - 1)) ** 1.2
        d = 0.16
        tt_ = A.tt(d)
        burst = A.filt(r.standard_normal(len(tt_)), 'band', [350, 2200]) * np.exp(-tt_ / 0.05) * A.env(len(tt_), 0.003, 0.03)
        thump = np.sin(2 * np.pi * 85 * tt_) * np.exp(-tt_ / 0.05) * 0.6
        x = (burst / (np.abs(burst).max() + 1e-9) + thump) * (1.0 - 0.45 * i / n)
        for side in (-1, 1):
            p = side * (0.15 + 0.7 * i / (n - 1))
            seg = A.pan(x, p) * 0.7
            j = n_(at + r.uniform(0, 0.03))
            out[j:j + len(seg)] += seg[:len(out) - j]
    return out


def chime():
    """C2 confirm: a clean two-note tone."""
    return np.concatenate([A.tone(1318.5, 0.11, 0.005, 0.06, (1.0, 0.3)), A.tone(1760.0, 0.24, 0.005, 0.16, (1.0, 0.3))])


# ---------------------------------------------------------------- music
def build_music_v51(vo_lens):
    m = A.load(V5 / 'music.mp3')[:n_(DUR)]
    m = np.pad(m, ((0, n_(DUR) - len(m)), (0, 0)))
    tt = np.arange(len(m)) / SR
    # 02: the score tightens under the radar (darker, a little lower)
    m = sweep_filter(m, t(7), t(16), 16000, 7000)
    m = sweep_filter(m, t(16), SINK[1], 5000, 260)
    m = tape_stop(m, SINK[1] - 0.6, SINK[1])  # 03: sinks to silence as the track goes dashed
    # 04: silence and a held tone (effects bus); the score comes back on the kick
    rest = A.load(V5 / 'music.mp3')[:n_(DUR)]
    rest = np.pad(rest, ((0, n_(DUR) - len(rest)), (0, 0)))
    m[n_(KICK) - 64:] = rest[n_(KICK) - 64:]
    m[n_(KICK) - 64:n_(KICK)] *= np.linspace(0, 1, 64)[:, None]
    # 08: builds into STOP (the low end drains away, then slams back)
    b = sweep_filter(m, BUILD[0], STOP - 0.02, 30, 700, kind='high')
    m[n_(BUILD[0]):n_(STOP)] = b[n_(BUILD[0]):n_(STOP)]
    # 11: the score dies with the engines; then only water
    m = tape_stop(m, *DIE)
    # 12: relief; the score comes back up muffled and opens toward the finale
    back = sweep_filter(rest, RETURN[0], RETURN[1] - 0.3, 240, 16000)
    i0 = n_(RETURN[0])
    m[i0:] = back[i0:]
    ride = np.interp(tt, [0, t(7), t(7) + 0.3, t(16), SINK[1], KICK - 0.01, KICK, BUILD[0], STOP - 0.02, STOP, RETURN[0], RETURN[1], 60],
                     [0.0, 0.0, 1.0, 1.5, -6.0, -6.0, 0.0, 0.0, 1.5, 0.5, -15.0, -1.0, 0.5])
    m *= (10 ** (ride / 20))[:, None]
    m[:n_(RETURN[0])] *= (tt[:n_(RETURN[0])] < DIE[1])[:, None]
    m[n_(END_CUT):] = 0  # 14: hard cut to navy
    m[n_(END_CUT) - n_(0.025):n_(END_CUT)] *= np.linspace(1, 0, n_(0.025))[:, None]
    return m * duck(vo_lens, 6.0, tt)


def duck(vo_lens, depth_db, tt, lead=0.15, tail=0.3):
    d = np.zeros(len(tt))
    for k, s in VO.items():
        e = s + vo_lens[k]
        d = np.maximum(d, depth_db * smoothstep((tt - (s - lead)) / lead) * (1 - smoothstep((tt - e) / tail)))
    return (10 ** (-d / 20))[:, None]


# ---------------------------------------------------------------- effects
def build_sfx_v51():
    b = Bus()
    impact, braam, whoosh, riser, suck = (norm(src4(n), -4, 'peak') for n in ('impact', 'braam', 'whoosh', 'riser', 'suck'))
    whoosh = norm(lp(whoosh, 6000), -6, 'peak')
    boom = st(norm(sub_boom(), -3, 'peak'))

    def hit(at, db=0.0, braam_db=-4.0, with_braam=True):
        db -= 4.0
        b.add(impact, at - 0.012, db)
        b.add(boom, at - 0.004, db - 2.0)
        if with_braam:
            b.add(fade(braam, 0.004, 0.9), at - 0.01, db + braam_db)

    def ping(at, f=1568.0, db=-17.0, p=0.0):
        b.add(panned(st(ui_ping(f)), p), at, db)

    def cut_whoosh(at, db=-14.0, p=0.0, rate=1.0):
        b.add(panned(speed(whoosh, rate), p) * 1.3, at - 0.16 / rate, db)

    sea = norm(src4('ocean_night'), -27)
    # ---- 01 the boat: outboards flat out from frame one (v4's checked clip), gone on the cut to the radar
    gofast = norm(src4('gofast'), -14)
    b.add(fade(loop(gofast, t(7) + 0.05, 0.5), 0.02, 0.06), 0.0, 0.0)
    hit(t(0) + 0.02, -6.0, with_braam=False)
    # ---- 02 detected and designated: inside the aircraft; radar sweep tone, muffled drone, console tones
    drone = st(A.aircraft_drone(MPA_BREAKS + 1.5 - t(7)))
    b.add(fade(norm(drone, -21), 0.08, 1.4), t(7), 0.0)
    for p_ in RADAR_PASSES:
        b.add(st(A.radar_sweep(0.75)), p_ - 0.62, -24.0)
    ping(CUE, 1175.0, -19.0)
    ping(HOOK, 1568.0, -16.0)
    ping(DETECTED, 1760.0, -18.0)
    b.add(st(chime()), DESIGNATED, -15.0)
    # ---- 03 no end game: the aircraft leaves; the sea; the score sinks away
    b.add(fade(loop(sea, SINK[1] - t(16) + 5.0, 1.2), 0.6, 1.5), t(16), 0.0)
    b.add(st(sub_boom(3.0, 30.0, 25.0, 1.2)), SINK[1] - 0.55, -14.0)
    # ---- 04 tasked: one held tone in the silence, markers blink on, two get tasked, then the score rebuilds
    held = st(A.held_tone(KICK - t(24) + 0.3))
    b.add(fade(held, 0.3, 0.4), t(24) - 0.2, -14.0)
    for i in range(20):
        b.add(st(A.blip(2093.0 + 90 * (i % 3), 0.025, 0.012)), FLEET_ON + ((i * 7) % 20) * 0.065, -31.0)
    b.add(st(chime()), TASK, -14.0)
    for i, p_ in enumerate((-0.4, 0.4)):
        b.add(panned(st(swish(0.45)), p_), INTERCEPT + 0.1 * i, -17.0)
    # no bright riser here: it sits in near-silence, and in this context the listening check heard a rising whine as a
    # possible 'electronic scream'. A low swell builds into the kick instead.
    b.add(st(sub_boom(2.2, 28.0, 0.0, 9.0))[::-1] * np.linspace(0, 1, n_(2.2))[:, None] ** 2, KICK, -9.0, end_at=True)
    b.add(fade(lp(norm(src4('underwater'), -14), 900), 1.2, 0.02)[:n_(2.4)], KICK, -6.0, end_at=True)
    b.add(fade(lp(suck[-n_(0.9):], 3000), 0.02, 0.005), KICK, -13.0, end_at=True)
    # ---- 05 lift: the kick; the fan spools to a full roar, it climbs onto the foils and is gone
    hit(KICK, 0.0)
    b.add(fade(lp(norm(src4('fan_spool'), -12), 3000), 0.03, 0.4), KICK - 0.05, -1.0)
    run = norm(lp(src4('run'), 3800), -16)
    roar = fade(loop(run, t(38) - t(33) + 0.3, 0.5), 0.5, 0.25)
    roar *= np.linspace(0.6, 1.2, len(roar))[:, None]
    b.add(roar, t(33), -2.0)
    b.add(fade(norm(src4('splash'), -8, 'peak'), 0.002, 0.3), t(33) + 0.5, -10.0)
    b.add(lp(panned(norm(src4('passby'), -8, 'peak'), np.linspace(-0.6, 0.9, len(src4('passby')))), 3200), t(36.4), -8.0)
    # ---- 06 converge: driving score; a data tone on each track update
    cut_whoosh(t(38), -15.0, 0.3)
    for i, u in enumerate(UPDATES):
        b.add(st(A.blip(1760.0 + 120 * i, 0.06, 0.03)), u, -15.0)
        b.add(st(A.blip(2637.0, 0.03, 0.015)), u + 0.09, -22.0)
    # ---- 07 eyes on: inside the sensor, then the fan drops to a hull-borne hum and the hull slaps
    hit(t(45), -6.0, with_braam=False)
    b.add(fade(st(B4.sensor_hum(IR_PULL - t(45))), 0.1, 0.2), t(45), -26.0)
    idle = norm(src4('idle'), -21)
    b.add(fade(loop(idle, t(54) - IR_PULL + 0.3, 0.8), 0.4, 0.2), IR_PULL, 0.0)
    b.add(fade(loop(norm(src5('hull_slap'), -22), t(54) - IR_PULL + 0.3, 0.8), 0.4, 0.2), IR_PULL, 0.0)
    # ---- 08 authorized: a single confirm tone; the plan draws itself; the score builds
    b.add(st(chime()), AUTHORIZED, -12.0)
    b.add(panned(st(swish(0.8, 300, 3000)), 0.3), PLAN + 0.1, -16.0)
    b.add(fade(lp(riser, 2200), 0.2, 0.005), STOP, -9.0, end_at=True)
    b.add(fade(lp(suck, 3500), 0.02, 0.005), STOP, -11.0, end_at=True)
    # ---- 09 pass: STOP; fan roar as it passes, the outboards answer
    hit(STOP, +1.0, -3.0)
    b.add(fade(loop(run, 2.4, 0.4), 0.3, 0.6), STOP + 0.2, -3.0)
    b.add(lp(panned(norm(src4('passby'), -6, 'peak'), np.linspace(-0.8, 0.8, len(src4('passby')))), 3200), STOP + 1.0, -6.0)
    b.add(lp(fade(loop(gofast, t(72) - (STOP + 1.9) + 0.1, 0.5), 0.5, 0.05), 4000), STOP + 1.9, -5.0)
    # ---- 10 net away: a sharp pneumatic thump; the net slaps the water
    b.add(fade(lp(norm(src5('net_launch'), -3, 'peak'), 6500), 0.002, 0.3), NET_FIRE - 0.01, -3.0)
    b.add(boom, NET_FIRE, -10.0)
    b.add(norm(net_splashes(), -3, 'peak'), NET_FIRE + 0.3, -9.0)
    b.add(lp(panned(st(swish(0.7, 200, 1500)), 0.6), 1800), NET_FIRE + 0.9, -20.0)  # Marlin peels off
    # ---- 11 fouled: the swerve at full throttle, the props foul, the outboards choke and die, then only water
    swerve = speed(norm(src4('gofast'), -14), 0.94)
    b.add(fade(loop(swerve, FOUL - t(72) + 0.25, 0.4), 0.02, 0.18), t(72), 1.0)
    cut_whoosh(t(72), -12.0, -0.3)
    bog = fade(norm(src5('engines_bog'), -14), 0.02, 0.5)
    b.add(bog, FOUL - 0.05, 0.0)
    b.add(fade(lp(norm(src5('prop_jam'), -16), 1800), 0.05, 0.4), FOUL - 0.1, -1.0)  # the cutaway, under water
    hit(FOUL, -7.0, with_braam=False)
    b.add(fade(loop(norm(src5('hull_slap'), -20), t(80) - (FOUL + 1.0) + 0.5, 0.8), 0.8, 0.4), FOUL + 1.0, 0.0)
    # ---- 12 hold: idle hum; a distant engine growing
    b.add(fade(loop(idle, t(88) - t(80) + 0.2, 0.8), 0.3, 0.3), t(80), -2.0)
    b.add(fade(loop(norm(src5('hull_slap'), -22), t(88) - t(80) + 0.2, 0.8), 0.3, 0.3), t(80), 0.0)
    partner = fade(norm(src5('partner'), -22), 1.0, 0.8)
    partner *= np.linspace(0.5, 1.4, len(partner))[:, None]
    b.add(panned(partner, 0.45), t(80) + 0.2, 0.0)
    # ---- 13 the fleet: the score resolves; three hits on the three words
    cut_whoosh(t(88), -12.0)
    for i in range(5):
        b.add(st(A.blip(1318.5, 0.05, 0.03)), RESPACE + 0.1 * i, -22.0)
    for i, w in enumerate(WORDS):
        b.add(panned(speed(whoosh, 0.85), 0.0), w - 0.3, -13.0)
        hit(w, +1.0 + 0.5 * i, -3.0)
    # ---- 14 end card: hard cut, a beat of silence, the logo lands, the name, a single fan spool-up to black
    b.add(st(norm(sub_boom(3.2, 30.0, 50.0, 1.0), -3, 'peak')), LOGO, -9.0)
    b.add(fade(lp(norm(src4('fan_spool'), -24), 2400), 0.6, 0.6), 60.0 - 1.95, 0.0)
    b.buf[n_(END_CUT):n_(LOGO) - n_(0.01)] *= 0.0
    b.buf[n_(END_CUT) - n_(0.02):n_(END_CUT)] *= np.linspace(1, 0, n_(0.02))[:, None]
    return b.buf


# ================================================================ v5.2 sound pass (option B): the audio never goes blank
# Client note on v5.1 B: the audio "shuts down weirdly" (0:13-0:14, 0:33, 0:56); the radar needs more sound; keep the
# tension at all times. So the score never switches off (it is pulled back and filtered where the story dips, then opens),
# a dark drone in the score's key (C#) and a ticking pulse run under the quiet stretches, every cut gets a transition,
# the radar gets a full designed layer, the build into STOP builds, and the end card rings out instead of cutting.
C_SHARP = 34.648  # C#1; the score sits in C# minor


def tension_drone(dur, seed=5):
    """Dark sustained bed in C#: sub, octave and fifth, slowly breathing, with low filtered air."""
    r = np.random.default_rng(seed)
    tt_ = A.tt(dur)
    x = np.zeros(len(tt_))
    for f, a in ((C_SHARP, 1.0), (2 * C_SHARP, 0.7), (3 * C_SHARP, 0.32), (4 * C_SHARP, 0.22), (6 * C_SHARP, 0.06)):
        for det in (-0.25, 0.0, 0.3):
            x += a * np.sin(2 * np.pi * (f + det) * tt_ + r.uniform(0, 6.28))
    x *= 1 + 0.18 * np.sin(2 * np.pi * 0.11 * tt_) + 0.08 * np.sin(2 * np.pi * 0.37 * tt_ + 1.0)
    air = A.filt(A.colored(dur, 1.2), 'low', 420) * (1 + 0.5 * np.sin(2 * np.pi * 0.07 * tt_))
    y = A.rms_norm(x, -20) + A.rms_norm(air, -30)
    return np.stack([y, np.roll(y, 37)], axis=1)


def tick(f_hi=4200.0, body=900.0, d=0.06):
    """One tick of the tension clock: a dry click with a little woody body."""
    tt_ = A.tt(d)
    click = A.filt(A.white(d), 'band', [f_hi * 0.6, min(f_hi * 1.6, SR / 2 - 200)]) * np.exp(-tt_ / 0.006)
    bod = np.sin(2 * np.pi * body * tt_) * np.exp(-tt_ / 0.012) * 0.5
    return (click / (np.abs(click).max() + 1e-9) + bod) * 0.8


def snare_roll(dur, seed=9):
    """A build: snare-like noise hits accelerating from quarter notes to thirty-seconds, swelling."""
    r = np.random.default_rng(seed)
    out = np.zeros(n_(dur + 0.2))
    tpos, step = 0.0, BEAT
    while tpos < dur:
        k = tpos / dur
        d = 0.09
        tt_ = A.tt(d)
        hitn = A.filt(r.standard_normal(len(tt_)), 'band', [900, 6000]) * np.exp(-tt_ / 0.03)
        hitn = hitn / (np.abs(hitn).max() + 1e-9) * (0.25 + 0.75 * k ** 1.3)
        i = n_(tpos)
        out[i:i + len(hitn)] += hitn[:len(out) - i]
        step = BEAT * (1.0 if k < 0.35 else 0.5 if k < 0.6 else 0.25 if k < 0.85 else 0.125)
        tpos += step
    return out


def dark_riser(dur):
    """Rising tension without a bright whine: a noise band and a sub tone climbing together, kept below 2.5 kHz."""
    tt_ = A.tt(dur)
    k = tt_ / dur
    f = 40 * (1 + 2.2 * k ** 1.6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR)
    noise = A.colored(dur, 1.0)
    out = np.zeros(len(tt_))
    for j in range(24):  # band rising 250 Hz -> 2.2 kHz
        a, b = int(j * len(tt_) / 24), int((j + 1) * len(tt_) / 24)
        c = 250 * (2200 / 250) ** ((j + 0.5) / 24)
        lo, hi = max(0, a - 2048), min(len(tt_), b + 2048)
        seg = A.filt(noise[lo:hi], 'band', [c * 0.6, c * 1.5])
        out[a:b] = seg[a - lo:a - lo + (b - a)]
    y = (A.rms_norm(out, -20) + A.rms_norm(sub, -22)) * k ** 1.8
    return y


def radar_ping(f=1400.0):
    """The contact painting on the scope: a crisp tone with a short echo."""
    p = A.tone(f, 0.09, 0.002, 0.07, (1.0, 0.35, 0.12))
    q = A.tone(f * 2, 0.04, 0.002, 0.03)
    p[:len(q)] += 0.5 * q
    return A.reverb(p, 0.5, 0.3)


def sweep_swoosh(dur=0.62, direction=1):
    """The beam sweeping across the sector: a soft band of air that pans with it."""
    x = swish(dur, 350, 2600)
    pans = np.linspace(-0.7 * direction, 0.7 * direction, len(x))
    return panned(st(x), pans)


def build_music(vo_lens):
    m = A.load(V5 / 'music.mp3')[:n_(DUR)]
    m = np.pad(m, ((0, n_(DUR) - len(m)), (0, 0)))
    tt = np.arange(len(m)) / SR
    # 02 radar: pulled back and a little darker so the radar reads
    m = sweep_filter(m, t(7), t(7) + 0.6, 16000, 6000)
    m[n_(t(7) + 0.6):n_(t(16))] = sweep_filter(m, t(7) + 0.6, t(16), 6000, 5000)[n_(t(7) + 0.6):n_(t(16))]
    # 03 the gap: the score sinks (darkens and drops) but keeps pulsing underneath; 04: it rebuilds into the kick
    m = sweep_filter(m, t(16), SINK[1], 5000, 320)
    m = sweep_filter(m, SINK[1], t(28), 320, 320)
    m = sweep_filter(m, t(28), KICK - 0.02, 320, 5000)
    # 11: the score dies with the engines (tape stop) ... and creeps straight back in, muffled, under the water
    rest = A.load(V5 / 'music.mp3')[:n_(DUR)]
    rest = np.pad(rest, ((0, n_(DUR) - len(rest)), (0, 0)))
    m = tape_stop(m, *DIE)
    back = sweep_filter(rest, DIE[1], t(80), 220, 420)
    back = sweep_filter(back, t(80), RETURN[1] - 0.3, 420, 16000)
    i0 = n_(DIE[1])
    fade_in = np.clip((tt[i0:] - DIE[1]) / 0.8, 0, 1)[:, None]
    m[i0:] = back[i0:] * fade_in
    # 14: no hard cut: the score darkens and recedes under the end card
    m = sweep_filter(m, END_CUT - 0.05, END_CUT + 1.1, 16000, 350)
    m[n_(END_CUT + 1.1):] = sweep_filter(m, END_CUT + 1.1, 60.0, 350, 200)[n_(END_CUT + 1.1):]
    ride = np.interp(tt, [0, t(7) - 0.05, t(7) + 0.4, t(16), SINK[1], t(28), KICK - 0.01, KICK, BUILD[0], STOP - 0.02, STOP,
                          DIE[1], t(80), RETURN[1], END_CUT, END_CUT + 1.2, 59.0, 60.0],
                     [0.0, 0.0, -3.0, -3.0, -7.5, -7.5, -3.0, 0.0, 0.0, 2.0, 0.5, -15.0, -11.0, -1.0, 0.5, -7.0, -12.0, -24.0])
    m *= (10 ** (ride / 20))[:, None]
    return m * duck(vo_lens, 6.0, tt)


def build_sfx():
    b = Bus()
    impact, braam, whoosh, riser, suck = (norm(src4(n), -4, 'peak') for n in ('impact', 'braam', 'whoosh', 'riser', 'suck'))
    whoosh = norm(lp(whoosh, 6000), -6, 'peak')
    boom = st(norm(sub_boom(), -3, 'peak'))

    def hit(at, db=0.0, braam_db=-4.0, with_braam=True):
        db -= 4.0
        b.add(impact, at - 0.012, db)
        b.add(boom, at - 0.004, db - 2.0)
        if with_braam:
            b.add(fade(braam, 0.004, 0.9), at - 0.01, db + braam_db)

    def ping(at, f=1568.0, db=-17.0, p=0.0):
        b.add(panned(st(ui_ping(f)), p), at, db)

    def cut_whoosh(at, db=-14.0, p=0.0, rate=1.0):
        b.add(panned(speed(whoosh, rate), p) * 1.3, at - 0.16 / rate, db)

    def swell(at, dur=0.9, db=-12.0):  # reverse swell sucking into a cut
        b.add(fade(lp(suck[-n_(dur):], 3500), 0.05, 0.005), at, db, end_at=True)

    def ticks(a, z, db=-22.0, accel_at=None):
        tpos = a
        while tpos < z:
            b.add(st(tick()), tpos, db)
            tpos += BEAT / 2 if accel_at is not None and tpos >= accel_at else BEAT

    # ---- the tension bed under the whole film: a C# drone that rises wherever the score dips
    tt = np.arange(n_(DUR)) / SR
    bed = tension_drone(DUR)
    lvl = np.interp(tt, [0, t(7), t(16), SINK[1], t(28), KICK, KICK + 1.0, BUILD[0], STOP, STOP + 0.5, FOUL, DIE[1], t(80), RETURN[1],
                         END_CUT - 0.5, END_CUT + 0.4, 58.5, 60.0],
                    [-40, -32, -26, -11, -12, -20, -34, -34, -26, -36, -36, -14, -16, -30, -32, -13, -11, -22])
    b.add(bed * (10 ** (lvl / 20))[:, None], 0.0, 0.0)
    sea = norm(src4('ocean_night'), -27)
    # ---- 01 the boat
    gofast = norm(src4('gofast'), -14)
    b.add(fade(loop(gofast, t(7) + 0.05, 0.5), 0.02, 0.12), 0.0, 0.0)
    hit(t(0) + 0.02, -6.0, with_braam=False)
    swell(t(7), 0.7, -12.0)  # sucked out of the boat ...
    b.add(st(sub_boom(1.8, 34.0, 40.0, 0.6)), t(7), -12.0)  # ... into the aircraft
    # ---- 02 radar: the full layer. Beam sweeps (panning with it), the contact painting on every pass, console hum, chatter
    drone = st(A.aircraft_drone(MPA_BREAKS + 1.5 - t(7)))
    b.add(fade(norm(drone, -21), 0.08, 1.4), t(7), 0.0)
    hum = st(A.filt(sum(np.sin(2 * np.pi * f * A.tt(t(16) - t(7))) * a for f, a in ((120, 1.0), (240, 0.4), (360, 0.15))), 'low', 800))
    b.add(fade(norm(hum, -30), 0.3, 0.8), t(7), 0.0)
    passes = [RADAR_PASSES[0] - 0.75] + RADAR_PASSES + [RADAR_PASSES[-1] + 0.75]
    for i, p_ in enumerate(passes):
        b.add(sweep_swoosh(0.62, 1 if i % 2 else -1), p_ - 0.31, -10.0)
        b.add(st(A.radar_sweep(0.75)), p_ - 0.62, -12.0)
    sonar = fade(lp(norm(src4('sonar'), -6, 'peak'), 5000), 0.002, 0.8)
    for i, p_ in enumerate(RADAR_PASSES):
        b.add(st(radar_ping(1400.0)), p_, -13.0 + 0.8 * i)  # the return holds, sweep after sweep
        b.add(sonar[:n_(1.2)], p_ + 0.005, -17.0 + 0.6 * i)  # with a deep echoing ping under it
    b.add(sonar, HOOK, -11.0)
    r = np.random.default_rng(21)
    for k in range(26):  # console data chatter
        b.add(st(A.blip(r.choice([2349.0, 2637.0, 3136.0]), 0.022, 0.01)), t(7) + 0.2 + r.uniform(0, t(16) - t(7) - 0.4), -27.0)
    b.add(st(A.blip(880.0, 0.05, 0.02)), CUE, -14.0)
    b.add(st(A.blip(1318.5, 0.05, 0.02)), CUE + 0.09, -14.0)
    for j in range(3):  # lock-on: the operator hooks the return
        b.add(st(A.blip(1760.0, 0.035, 0.015)), HOOK + 0.07 * j, -12.0)
    b.add(st(chime()), DETECTED, -13.0)
    b.add(st(chime()), DESIGNATED, -10.0)
    hit(DESIGNATED, -14.0, with_braam=False)
    # ---- 03 no end game: the aircraft leaves, the sea, the score sinks; the clock starts
    cut_whoosh(t(16), -15.0, 0.3)
    b.add(fade(loop(sea, KICK - t(16) + 0.5, 1.2), 0.6, 1.0), t(16), 2.0)
    b.add(st(sub_boom(3.0, 30.0, 25.0, 1.2)), SINK[1] - 0.55, -12.0)
    sink = A.tt(1.6)
    b.add(st(np.sin(2 * np.pi * np.cumsum(110 * (0.5 ** (sink / 1.6))) / SR) * A.env(len(sink), 0.05, 0.4)), SINK[1] - 1.2, -24.0)  # falling tone
    ticks(t(18), KICK - 0.05, -21.0, accel_at=t(28))
    swell(SINK[1] - 0.5, 1.4, -11.0)  # the track goes dashed: sucked down into the boom
    b.add(fade(lp(norm(src4('underwater'), -14), 1200), 0.6, 1.2)[:n_(3.0)], SINK[1] - 1.4, -4.0)
    for k in np.arange(SINK[1], KICK - 0.3, 2 * BEAT):
        b.add(st(norm(heartbeat(), -3, 'peak')), k, -15.0)
    # ---- 04 tasked: held tone (now in C#), markers blink on, two tasked, the score rebuilds into the kick
    held = st(A.held_tone(KICK - t(24) + 0.3))
    held = speed(held, 138.59 / 146.83)  # retuned from D to the score's C#
    b.add(fade(held, 0.6, 0.4), t(24), -18.0)
    for i in range(20):
        b.add(st(A.blip(2093.0 + 90 * (i % 3), 0.025, 0.012)), FLEET_ON + ((i * 7) % 20) * 0.065, -22.0)
    b.add(norm(dark_riser(0.9), -6, 'peak'), FLEET_ON + 0.1, -18.0, end_at=True)  # the fleet powers up on the display
    b.add(st(sub_boom(2.0, 36.0, 20.0, 0.8)), FLEET_ON + 0.1, -13.0)
    b.add(st(chime()), TASK, -12.0)
    for i, p_ in enumerate((-0.4, 0.4)):
        b.add(panned(st(swish(0.45)), p_), INTERCEPT + 0.1 * i, -15.0)
    b.add(norm(dark_riser(KICK - t(28)), -6, 'peak'), KICK, -14.0, end_at=True)
    b.add(st(sub_boom(2.2, 28.0, 0.0, 9.0))[::-1] * np.linspace(0, 1, n_(2.2))[:, None] ** 2, KICK, -9.0, end_at=True)
    swell(KICK, 0.9, -13.0)
    # ---- 05 lift
    hit(KICK, 0.0)
    b.add(fade(lp(norm(src4('fan_spool'), -12), 3000), 0.03, 0.4), KICK - 0.05, -1.0)
    run = norm(lp(src4('run'), 3800), -16)
    roar = fade(loop(run, t(38) - t(33) + 0.3, 0.5), 0.5, 0.25)
    roar *= np.linspace(0.6, 1.2, len(roar))[:, None]
    b.add(roar, t(33), -2.0)
    b.add(fade(norm(src4('splash'), -8, 'peak'), 0.002, 0.3), t(33) + 0.5, -10.0)
    b.add(lp(panned(norm(src4('passby'), -8, 'peak'), np.linspace(-0.6, 0.9, len(src4('passby')))), 3200), t(36.4), -8.0)
    # ---- 06 converge
    cut_whoosh(t(38), -13.0, 0.3)
    b.add(fade(loop(run, t(45) - t(38), 0.5), 0.4, 0.4), t(38), -16.0)  # the two Marlins running, under the display
    for i, u in enumerate(UPDATES):
        b.add(st(A.blip(1760.0 + 120 * i, 0.06, 0.03)), u, -13.0)
        b.add(st(A.blip(2637.0, 0.03, 0.015)), u + 0.09, -20.0)
    # ---- 07 eyes on
    hit(t(45), -6.0, with_braam=False)
    b.add(fade(st(B4.sensor_hum(IR_PULL - t(45))), 0.1, 0.2), t(45), -22.0)
    idle = norm(src4('idle'), -21)
    b.add(fade(loop(idle, t(54) - IR_PULL + 0.3, 0.8), 0.4, 0.2), IR_PULL, 0.0)
    b.add(fade(loop(norm(src5('hull_slap'), -22), t(54) - IR_PULL + 0.3, 0.8), 0.4, 0.2), IR_PULL, 0.0)
    cut_whoosh(IR_PULL, -17.0, 0.4)
    # ---- 08 authorized: confirm tone; the plan draws; a real build into STOP
    cut_whoosh(t(54), -14.0, -0.3)
    b.add(st(chime()), AUTHORIZED, -11.0)
    b.add(panned(st(swish(0.8, 300, 3000)), 0.3), PLAN + 0.1, -15.0)
    b.add(st(snare_roll(STOP - BUILD[0])), BUILD[0], -17.0)
    b.add(norm(dark_riser(STOP - t(55)), -6, 'peak'), STOP, -12.0, end_at=True)
    b.add(st(sub_boom(2.6, 28.0, 0.0, 9.0))[::-1] * np.linspace(0, 1, n_(2.6))[:, None] ** 2, STOP, -8.0, end_at=True)
    swell(STOP, 1.2, -10.0)
    # ---- 09 pass
    hit(STOP, +1.0, -3.0)
    b.add(fade(loop(run, 2.4, 0.4), 0.3, 0.6), STOP + 0.2, -3.0)
    b.add(lp(panned(norm(src4('passby'), -6, 'peak'), np.linspace(-0.8, 0.8, len(src4('passby')))), 3200), STOP + 1.0, -6.0)
    b.add(lp(fade(loop(gofast, t(72) - (STOP + 1.9) + 0.1, 0.5), 0.5, 0.05), 4000), STOP + 1.9, -5.0)
    # ---- 10 net away
    cut_whoosh(t(66), -14.0, 0.3)
    b.add(fade(lp(norm(src5('net_launch'), -3, 'peak'), 6500), 0.002, 0.3), NET_FIRE - 0.01, -3.0)
    b.add(boom, NET_FIRE, -10.0)
    b.add(norm(net_splashes(), -3, 'peak'), NET_FIRE + 0.3, -9.0)
    b.add(lp(panned(st(swish(0.7, 200, 1500)), 0.6), 1800), NET_FIRE + 0.9, -20.0)
    # ---- 11 fouled: the engines choke and die; the drone and a heartbeat carry the tension, the score creeps back
    swerve = speed(norm(src4('gofast'), -14), 0.94)
    b.add(fade(loop(swerve, FOUL - t(72) + 0.25, 0.4), 0.02, 0.18), t(72), 1.0)
    cut_whoosh(t(72), -12.0, -0.3)
    b.add(fade(norm(src5('engines_bog'), -14), 0.02, 0.5), FOUL - 0.05, 0.0)
    b.add(fade(lp(norm(src5('prop_jam'), -16), 1800), 0.05, 0.4), FOUL - 0.1, -1.0)
    hit(FOUL, -7.0, with_braam=False)
    b.add(fade(loop(norm(src5('hull_slap'), -20), t(80) - (FOUL + 1.0) + 0.5, 0.8), 0.8, 0.4), FOUL + 1.0, 0.0)
    for k in np.arange(DIE[1] + 0.2, RETURN[1] - 0.5, 2 * BEAT):
        b.add(st(norm(heartbeat(), -3, 'peak')), k, -14.0)
    ticks(t(80), RETURN[1] - 0.1, -25.0, accel_at=t(86))
    # ---- 12 hold
    swell(t(80), 0.8, -15.0)
    b.add(fade(loop(idle, t(88) - t(80) + 0.2, 0.8), 0.3, 0.3), t(80), -2.0)
    b.add(fade(loop(norm(src5('hull_slap'), -22), t(88) - t(80) + 0.2, 0.8), 0.3, 0.3), t(80), 0.0)
    partner = fade(norm(src5('partner'), -22), 1.0, 0.8)
    partner *= np.linspace(0.5, 1.4, len(partner))[:, None]
    b.add(panned(partner, 0.45), t(80) + 0.2, 0.0)
    b.add(norm(dark_riser(RETURN[1] - t(86)), -6, 'peak'), RETURN[1], -16.0, end_at=True)
    # ---- 13 the fleet: three hits on the three words
    cut_whoosh(t(88), -12.0)
    for i in range(5):
        b.add(st(A.blip(1318.5, 0.05, 0.03)), RESPACE + 0.1 * i, -20.0)
    for i, w in enumerate(WORDS):
        b.add(panned(speed(whoosh, 0.85), 0.0), w - 0.3, -13.0)
        hit(w, +1.0 + 0.5 * i, -3.0)
    # ---- 14 end card: the last hit rings into the logo; the name; a low spool-up to black. Never empty.
    swell(LOGO, 0.9, -11.0)
    hit(LOGO, -3.0, -6.0)
    b.add(st(norm(sub_boom(3.6, 30.0, 50.0, 1.4), -3, 'peak')), LOGO, -8.0)
    b.add(fade(lp(braam, 1200), 0.01, 2.0), LOGO, -14.0)  # a dark second layer under the logo hit
    b.add(fade(lp(norm(src4('fan_spool'), -19), 2400), 0.5, 0.5), 60.0 - 2.1, 0.0)
    b.add(st(sub_boom(1.2, 32.0, 30.0, 0.5)), 59.55, -12.0)
    return b.buf


# ---------------------------------------------------------------- narration
def build_vo():
    chain = Pedalboard([HighpassFilter(75), PeakFilter(180, gain_db=1.5, q=0.9), PeakFilter(3000, gain_db=3.0, q=0.8),
                        HighShelfFilter(8000, gain_db=2.0), Compressor(threshold_db=-22, ratio=4.0, attack_ms=3, release_ms=110), Gain(5.0)])
    verb = Pedalboard([Reverb(room_size=0.3, damping=0.55, wet_level=0.09, dry_level=1.0, width=0.9)])
    out = np.zeros((n_(DUR), 2))
    lens = {}
    for k, at in VO.items():
        x, sr = sf.read(VO_DIR / f'{k}.wav', dtype='float32')
        assert sr == SR
        x = norm(x, -20.0)
        if k in ('l5a', 'l5b', 'l5c', 'l6'):
            x = x * 10 ** (1.5 / 20)
        y = chain(x[None, :], SR)
        y = verb(np.repeat(y, 2, axis=0), SR).T
        lens[k] = len(x) / SR
        i0 = n_(at)
        out[i0:i0 + len(y)] += y[:len(out) - i0]
    return out, lens


# option B (v5.1): the same mix with another narration folder; every file it writes carries the tag
VO_DIR = V5 / 'vo'
TAG = ''
if '--vo' in sys.argv:
    VO_DIR = pathlib.Path(sys.argv[sys.argv.index('--vo') + 1]).resolve()
if '--tag' in sys.argv:
    TAG = '_' + sys.argv[sys.argv.index('--tag') + 1]
TARGET_LUFS = -14.0
CEILING = 10 ** (-3.0 / 20)


def master(music, sfx, vo):
    """Glue compression and a brick-wall limiter, with the gain found by measurement so the film lands at -14 LUFS without
    levelling the dynamics (the silences and the build must survive)."""
    mix = ((music + sfx + vo) * 10 ** (-6.0 / 20)).astype(np.float32)
    glue = Pedalboard([HighpassFilter(28), Compressor(threshold_db=-16, ratio=1.6, attack_ms=30, release_ms=250)])
    limiter = Pedalboard([Limiter(threshold_db=-2.6, release_ms=90)])
    pre = glue(mix.T, SR)
    gain_db = 0.0
    for _ in range(5):
        out = np.clip(limiter(pre * 10 ** (gain_db / 20), SR).T, -CEILING, CEILING)
        sf.write(V5 / f'mix_premaster{TAG}.wav', out, SR, subtype='PCM_24')
        i_lufs, lra, peak, curve = B4.loudness(V5 / f'mix_premaster{TAG}.wav')
        if abs(TARGET_LUFS - i_lufs) < 0.15:
            break
        gain_db += TARGET_LUFS - i_lufs
    out[-n_(0.9):] *= (np.linspace(1, 0, n_(0.9)) ** 1.5)[:, None]  # the film decays into black instead of stopping
    sf.write(V5 / f'mix_premaster{TAG}.wav', out, SR, subtype='PCM_24')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V5 / f'mix_premaster{TAG}.wav'), '-ar', str(SR), '-c:a', 'flac', '-sample_fmt', 's16', str(V5 / f'mix{TAG}.flac')], check=True)
    i_lufs, lra, peak, curve = B4.loudness(V5 / f'mix{TAG}.flac')
    print(f'master gain {gain_db:+.1f} dB -> {i_lufs:.1f} LUFS, LRA {lra:.1f} LU, true peak {peak:.1f} dBFS')
    print('short-term loudness every 3 s:', ' '.join(f'{v:.0f}' for v in curve))


def main():
    if '--master-only' in sys.argv:
        music, sfx, vo = (sf.read(V5 / f'{n}{TAG}.wav', dtype='float64')[0] for n in ('music', 'sfx', 'vo'))
        return master(music, sfx, vo)
    vo, vo_lens = build_vo()
    v51 = '--v51' in sys.argv  # the v5.0 / v5.1 design (option A as delivered)
    music = (build_music_v51 if v51 else build_music)(vo_lens) * 10 ** (-2.0 / 20)
    tt = np.arange(n_(DUR)) / SR
    sfx = (build_sfx_v51 if v51 else build_sfx)() * duck(vo_lens, 5.0, tt)
    for name, x in (('music', music), ('sfx', sfx), ('vo', vo)):
        sf.write(V5 / f'{name}{TAG}.wav', x, SR, subtype='FLOAT')
    json.dump(dict(beat=BEAT, t0=T0, vo=VO, vo_lens=vo_lens), open(V5 / f'timeline{TAG}.json', 'w'), indent=1)
    print('sec   sfx  music    vo')
    for s in range(60):
        row = [20 * np.log10(np.sqrt(np.mean(x[n_(s):n_(s + 1)] ** 2)) + 1e-9) for x in (sfx, music, vo)]
        print(f'{s:3d} ' + ' '.join(f'{v:6.1f}' if v > -90 else '   -- ' for v in row))
    master(music, sfx, vo)


if __name__ == '__main__':
    main()
