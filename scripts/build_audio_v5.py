"""Animatic v5.0 soundtrack (Storyboard V7): score + designed sound + narrator on the score's beat grid, mastered.

  /opt/venv-audio/bin/python scripts/build_audio_v5.py            # build stems and master
  /opt/venv-audio/bin/python scripts/build_audio_v5.py --master-only

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
def build_music(vo_lens):
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
    b.add(fade(held, 0.6, 0.4), t(24), -18.0)
    for i in range(20):
        b.add(st(A.blip(2093.0 + 90 * (i % 3), 0.025, 0.012)), FLEET_ON + ((i * 7) % 20) * 0.065, -31.0)
    b.add(st(chime()), TASK, -14.0)
    for i, p_ in enumerate((-0.4, 0.4)):
        b.add(panned(st(swish(0.45)), p_), INTERCEPT + 0.1 * i, -17.0)
    b.add(fade(riser, 0.02, 0.005), KICK, -8.0, end_at=True)
    b.add(fade(suck[-n_(0.9):], 0.02, 0.005), KICK, -11.0, end_at=True)
    # ---- 05 lift: the kick; the fan spools to a full roar, it climbs onto the foils and is gone
    hit(KICK, 0.0)
    b.add(fade(norm(src4('fan_spool'), -12), 0.03, 0.4), KICK - 0.05, -1.0)
    run = norm(lp(src4('run'), 5500), -16)
    roar = fade(loop(run, t(38) - t(33) + 0.3, 0.5), 0.5, 0.25)
    roar *= np.linspace(0.6, 1.2, len(roar))[:, None]
    b.add(roar, t(33), -2.0)
    b.add(fade(norm(src4('splash'), -8, 'peak'), 0.002, 0.3), t(33) + 0.5, -10.0)
    b.add(lp(panned(norm(src4('passby'), -8, 'peak'), np.linspace(-0.6, 0.9, len(src4('passby')))), 4200), t(36.4), -8.0)
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
    b.add(fade(riser, 0.02, 0.005), STOP, -7.0, end_at=True)
    b.add(fade(suck, 0.02, 0.005), STOP, -10.0, end_at=True)
    # ---- 09 pass: STOP; fan roar as it passes, the outboards answer
    hit(STOP, +1.0, -3.0)
    b.add(fade(loop(run, 2.4, 0.4), 0.3, 0.6), STOP + 0.2, -3.0)
    b.add(lp(panned(norm(src4('passby'), -6, 'peak'), np.linspace(-0.8, 0.8, len(src4('passby')))), 4200), STOP + 1.0, -6.0)
    b.add(lp(fade(loop(gofast, t(72) - (STOP + 1.9) + 0.1, 0.5), 0.5, 0.05), 5500), STOP + 1.9, -5.0)
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


# ---------------------------------------------------------------- narration
def build_vo():
    chain = Pedalboard([HighpassFilter(75), PeakFilter(180, gain_db=1.5, q=0.9), PeakFilter(3000, gain_db=3.0, q=0.8),
                        HighShelfFilter(8000, gain_db=2.0), Compressor(threshold_db=-22, ratio=4.0, attack_ms=3, release_ms=110), Gain(5.0)])
    verb = Pedalboard([Reverb(room_size=0.3, damping=0.55, wet_level=0.09, dry_level=1.0, width=0.9)])
    out = np.zeros((n_(DUR), 2))
    lens = {}
    for k, at in VO.items():
        x, sr = sf.read(V5 / 'vo' / f'{k}.wav', dtype='float32')
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
        sf.write(V5 / 'mix_premaster.wav', out, SR, subtype='PCM_24')
        i_lufs, lra, peak, curve = B4.loudness(V5 / 'mix_premaster.wav')
        if abs(TARGET_LUFS - i_lufs) < 0.15:
            break
        gain_db += TARGET_LUFS - i_lufs
    out[-n_(0.3):] *= np.linspace(1, 0, n_(0.3))[:, None]
    sf.write(V5 / 'mix_premaster.wav', out, SR, subtype='PCM_24')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V5 / 'mix_premaster.wav'), '-ar', str(SR), '-c:a', 'flac', '-sample_fmt', 's16', str(V5 / 'mix.flac')], check=True)
    i_lufs, lra, peak, curve = B4.loudness(V5 / 'mix.flac')
    print(f'master gain {gain_db:+.1f} dB -> {i_lufs:.1f} LUFS, LRA {lra:.1f} LU, true peak {peak:.1f} dBFS')
    print('short-term loudness every 3 s:', ' '.join(f'{v:.0f}' for v in curve))


def main():
    if '--master-only' in sys.argv:
        music, sfx, vo = (sf.read(V5 / f'{n}.wav', dtype='float64')[0] for n in ('music', 'sfx', 'vo'))
        return master(music, sfx, vo)
    vo, vo_lens = build_vo()
    music = build_music(vo_lens) * 10 ** (-2.0 / 20)
    tt = np.arange(n_(DUR)) / SR
    sfx = build_sfx() * duck(vo_lens, 5.0, tt)
    for name, x in (('music', music), ('sfx', sfx), ('vo', vo)):
        sf.write(V5 / f'{name}.wav', x, SR, subtype='FLOAT')
    json.dump(dict(beat=BEAT, t0=T0, vo=VO, vo_lens=vo_lens), open(V5 / 'timeline.json', 'w'), indent=1)
    print('sec   sfx  music    vo')
    for s in range(60):
        row = [20 * np.log10(np.sqrt(np.mean(x[n_(s):n_(s + 1)] ** 2)) + 1e-9) for x in (sfx, music, vo)]
        print(f'{s:3d} ' + ' '.join(f'{v:6.1f}' if v > -90 else '   -- ' for v in row))
    master(music, sfx, vo)


if __name__ == '__main__':
    main()
