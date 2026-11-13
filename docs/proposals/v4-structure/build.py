"""Build the "new structure" proposal PDF (visual, very little text) from the 13 Nov client audio note.

  python3 docs/proposals/v4-structure/build.py

Writes index.html next to this file and prints it to Marlin_New_Structure.pdf with the pre-installed Chromium.
Pages are 1280x720 (16:9 slides). Images are in img/ (frames from the Blender previz + two new stills).
"""
import math, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
FONTS = ROOT / 'public/fonts'

NAVY, PANEL, WHITE, STEEL, TEAL, ORANGE = '#0B1622', '#12202E', '#F4F6F8', '#8FA3B5', '#4FD1C5', '#F08A3C'

# ---------------------------------------------------------------- map diagrams (same language as the film's display)
C = (400.0, 118.0)  # contact
UL = math.hypot(-0.66, 0.75)
U = (-0.66 / UL, 0.75 / UL)  # its course, toward the coast
N = (0.75 / UL, 0.66 / UL)
STATIONS = [(70, 50), (190, 50), (300, 46), (520, 50), (610, 62), (130, 130), (40, 150), (560, 135), (60, 215), (180, 215),
            (440, 215), (570, 215), (120, 295), (240, 295), (360, 300), (480, 295), (600, 290), (630, 150), (480, 122)]
A = (C[0] + U[0] * 130, C[1] + U[1] * 130)  # the one dead ahead on the projected track
B = (250.0, 128.0)
D = (440.0, 215.0)
Q = (C[0] + U[0] * 40, C[1] + U[1] * 40)  # where the boat will be
AHEAD = (Q[0] + U[0] * 38, Q[1] + U[1] * 38)
LEFT = (Q[0] - N[0] * 40, Q[1] - N[1] * 40)
RIGHT = (Q[0] + N[0] * 40, Q[1] + N[1] * 40)
COAST = 'M0 338 C 110 322, 200 352, 320 336 S 500 322, 640 334 L640 360 L0 360 Z'


def base(extra='', rings=False, ring_set=None, dim_fleet=False):
    grid = ''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="360" stroke="#172839" stroke-width="1"/>' for x in range(0, 641, 64))
    grid += ''.join(f'<line x1="0" y1="{y}" x2="640" y2="{y}" stroke="#172839" stroke-width="1"/>' for y in range(0, 361, 60))
    fleet = ''
    for (x, y) in STATIONS:
        if rings:
            fleet += f'<circle cx="{x}" cy="{y}" r="74" fill="{TEAL}" fill-opacity="0.035" stroke="{TEAL}" stroke-opacity="0.22" stroke-width="1"/>'
    for (x, y) in STATIONS:
        o = 0.45 if dim_fleet else 0.95
        fleet += f'<ellipse cx="{x}" cy="{y}" rx="9" ry="4.5" fill="none" stroke="{TEAL}" stroke-opacity="{o * 0.5}" stroke-width="1"/>'
        fleet += f'<circle cx="{x}" cy="{y}" r="4.2" fill="{TEAL}" opacity="{o}"/>'
    hist = f'<line x1="{C[0] - U[0] * 170}" y1="{C[1] - U[1] * 170}" x2="{C[0]}" y2="{C[1]}" stroke="{ORANGE}" stroke-width="2.4"/>'
    proj_end = (C[0] + U[0] * 290, C[1] + U[1] * 290)
    proj = f'<line x1="{C[0]}" y1="{C[1]}" x2="{proj_end[0]}" y2="{proj_end[1]}" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="8 6" opacity="0.85"/>'
    contact = f'<g transform="translate({C[0]} {C[1]}) rotate(45)"><rect x="-8" y="-8" width="16" height="16" fill="{ORANGE}"/></g>'
    return (f'<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">'
            f'<rect width="640" height="360" fill="#0D1824"/>{grid}<path d="{COAST}" fill="#11283A" stroke="#3C5A73" stroke-width="1.5"/>'
            f'{fleet}{hist}{proj}{extra}{contact}</svg>')


def marlin(p, hot=True):
    r = 7 if hot else 4.2
    ring = f'<circle cx="{p[0]}" cy="{p[1]}" r="13" fill="none" stroke="{TEAL}" stroke-width="2"/>' if hot else ''
    return f'<circle cx="{p[0]}" cy="{p[1]}" r="{r}" fill="{TEAL}"/>{ring}'


def arrow(a, b, color=TEAL, w=3.2):
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    return (f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M0 0 L-13 -6.5 L-13 6.5 Z" fill="{color}" transform="translate({b[0]} {b[1]}) rotate({ang})"/>')


def label(x, y, text, color=WHITE, size=13, anchor='start'):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="IBM Plex Mono" font-size="{size}" letter-spacing="1.2" text-anchor="{anchor}" '
            f'paint-order="stroke" stroke="#0D1824" stroke-width="4">{text}</text>')


def map_detect():
    b = 26
    hook = ''.join(f'<path d="M {C[0] + sx * b} {C[1] + sy * (b - 10)} L {C[0] + sx * b} {C[1] + sy * b} L {C[0] + sx * (b - 10)} {C[1] + sy * b}" '
                   f'fill="none" stroke="{ORANGE}" stroke-width="2.6"/>' for sx in (-1, 1) for sy in (-1, 1))
    pulse = f'<circle cx="{C[0]}" cy="{C[1]}" r="44" fill="none" stroke="{ORANGE}" stroke-opacity="0.35" stroke-width="1.5"/>'
    hot = ''.join(marlin(p) + f'<circle cx="{p[0]}" cy="{p[1]}" r="74" fill="{TEAL}" fill-opacity="0.07" stroke="{TEAL}" stroke-opacity="0.75" stroke-width="1.6"/>' for p in (A, B, D))
    return base(pulse + hook + hot + label(C[0] + 34, C[1] - 16, 'TOI-01 · GO-FAST', ORANGE) + label(A[0] - 16, A[1] + 28, 'NEAREST MARLINS', TEAL, anchor='end'), dim_fleet=True)


def map_isolate():
    def short(a, b, k=0.9):
        return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    tg = ''.join(f'<circle cx="{p[0]}" cy="{p[1]}" r="9" fill="none" stroke="{TEAL}" stroke-width="1.8" stroke-dasharray="4 3"/>' for p in (AHEAD, LEFT, RIGHT))
    ar = arrow(A, short(A, AHEAD)) + arrow(B, short(B, LEFT)) + arrow(D, short(D, RIGHT))
    ms = ''.join(marlin(p) for p in (A, B, D))
    return base(tg + ar + ms + label(C[0] + 22, C[1] - 14, 'TOI-01', ORANGE) + label(A[0] - 18, A[1] + 26, 'HEAD-ON', TEAL, anchor='end')
                + label(B[0] - 18, B[1] - 14, 'FLANK', TEAL, anchor='end') + label(D[0] + 18, D[1] + 22, 'FLANK', TEAL), dim_fleet=True)


def map_surveil():
    box = f'<path d="M {AHEAD[0]} {AHEAD[1]} L {LEFT[0]} {LEFT[1]} L {C[0] - U[0] * 26} {C[1] - U[1] * 26} L {RIGHT[0]} {RIGHT[1]} Z" fill="{TEAL}" fill-opacity="0.10" stroke="{TEAL}" stroke-opacity="0.6" stroke-width="1.4" stroke-dasharray="5 4"/>'
    ms = ''.join(marlin(p) for p in (AHEAD, LEFT, RIGHT))
    los = ''.join(f'<line x1="{p[0]}" y1="{p[1]}" x2="{C[0]}" y2="{C[1]}" stroke="{TEAL}" stroke-width="1.4" stroke-dasharray="3 4" opacity="0.9"/>' for p in (AHEAD, LEFT, RIGHT))
    P = (585.0, 170.0)
    partner = (f'<line x1="640" y1="{P[1] + 14}" x2="{P[0]}" y2="{P[1]}" stroke="{WHITE}" stroke-width="1.8" stroke-dasharray="7 5"/>'
               + arrow(P, (P[0] - 70, P[1] - 14), WHITE, 1.8)
               + f'<rect x="{P[0] - 8}" y="{P[1] - 8}" width="16" height="16" fill="#0D1824" stroke="{WHITE}" stroke-width="2"/>'
               + label(P[0] - 4, P[1] + 30, 'PARTNER', WHITE, anchor='middle'))
    return base(box + los + ms + partner + label(C[0] + 22, C[1] - 14, 'TOI-01', ORANGE) + label(LEFT[0] - 20, LEFT[1] - 12, 'LIVE', TEAL, anchor='end'), dim_fleet=True)


def map_cover():
    ms = ''.join(marlin(p) for p in (AHEAD, LEFT, RIGHT))
    moves = ''
    for (x, y) in ((180, 215), (240, 295), (360, 300), (300, 46)):
        tx, ty = x + (A[0] - x) * 0.32, y + (A[1] - y) * 0.32
        moves += arrow((x, y), (tx, ty), WHITE, 1.8)
    return base(ms + moves, rings=True)


# ---------------------------------------------------------------- page helpers
def img(name, cls='', style=''):
    return f'<img class="{cls}" style="{style}" src="img/{name}.jpg">'


def footer(n, total):
    return f'<div class="foot"><span>ARCHIMEDES FREIGHT · MARLIN · NEW STRUCTURE · PROPOSAL FOR APPROVAL</span><span>{n} / {total}</span></div>'


def end_card(scale=1.0):
    return f'''<div class="endcard"><img src="img/logo.png" style="width:{150 * scale}px">
      <div class="ec-name" style="font-size:{46 * scale}px">MARLIN</div>
      <div class="ec-tag" style="font-size:{15 * scale}px">Detect. Isolate. Surveil.</div><div class="ec-rule"></div></div>'''


def timeline(segments, first_marlin, label_text):
    """segments: (seconds, kind, label). kinds: threat, marlin, map, end."""
    cells = ''.join(f'<div class="seg {k}" style="flex:{s}"><span>{l}</span></div>' for s, k, l in segments)
    ticks = ''.join(f'<span style="left:{t / 60 * 100}%">0:{t:02d}</span>' for t in range(0, 61, 10))
    return f'''<div class="tl"><div class="tl-bar">{cells}</div>
      <div class="tl-marker" style="left:{first_marlin / 60 * 100}%"><div class="tl-flag">{label_text}</div></div>
      <div class="tl-ticks">{ticks}</div></div>'''


def build():
    pages = []
    # ---- 1 cover
    pages.append(f'''<section class="page cover">{img('waits_close', 'bg')}
      <div class="shade"></div>
      <div class="cover-text"><img src="img/logo.png" class="logo">
        <div class="kicker">MARLIN · 60-SECOND FILM</div>
        <h1>New structure</h1>
        <div class="three"><b>Detect.</b> <b>Isolate.</b> <b>Surveil.</b></div>
        <div class="sub">Proposal for approval · built from your audio note of 13 Nov</div></div></section>''')

    # ---- 2 what you asked for
    mute = ('<svg viewBox="0 0 100 100"><path d="M18 40 h18 l22 -18 v56 l-22 -18 h-18 z" fill="#8FA3B5"/>'
            '<line x1="68" y1="36" x2="92" y2="64" stroke="#F08A3C" stroke-width="7" stroke-linecap="round"/>'
            '<line x1="92" y1="36" x2="68" y2="64" stroke="#F08A3C" stroke-width="7" stroke-linecap="round"/></svg>')
    top = f'''<div class="wtile"><div class="tile-n">1</div><div class="wt-body"><span class="strike">Cover. Sprint. Persist.</span>
        <span class="arrow-r">→</span><span class="newwords">Detect. Isolate. Surveil.</span></div><div class="wt-cap">New three words</div></div>
      <div class="wtile"><div class="tile-n">2</div><div class="wt-body"><div class="mute">{mute}</div></div><div class="wt-cap">No buzz at the end</div></div>'''
    pics = [('hook_bow', '3', 'Hook first: the threat'), ('waits_close', '4', 'Then Marlin: the apex predator'), ('vector', '5', 'Multiple Marlins vectoring in')]
    bottom = ''.join(f'<div class="ptile"><div class="pt-img">{img(n)}</div><div class="pt-cap"><span>{k}</span>{t}</div></div>' for n, k, t in pics)
    pages.append(f'<section class="page"><h2>What you asked for</h2><div class="wtiles">{top}</div><div class="ptiles">{bottom}</div>__FOOT__</section>')

    # ---- 3 timelines
    now = [(4, 'threat', 'Drug boat'), (3, 'threat', 'Radar'), (3, 'threat', 'IR ID'), (6, 'threat', 'Out of reach'), (4, 'map', 'Map'),
           (8, 'marlin', 'Marlin'), (6, 'map', 'Map'), (12, 'marlin', 'Marlin'), (10, 'map', 'Map'), (4, 'end', 'End')]
    new = [(4, 'threat', 'Hook'), (7, 'marlin', 'Marlin waits'), (8, 'map', 'DETECT'), (12, 'marlin', 'ISOLATE'), (14, 'marlin', 'SURVEIL'),
           (8, 'map', 'Coverage'), (7, 'end', 'End')]
    pages.append(f'''<section class="page"><h2>Marlin arrives at <em>0:04</em>, not 0:20</h2>
      <div class="tl-row"><div class="tl-name">NOW<br><small>v3.0</small></div>{timeline(now, 20, 'First Marlin · 0:20')}</div>
      <div class="tl-row"><div class="tl-name new">NEW</div>{timeline(new, 4, 'First Marlin · 0:04')}</div>
      <div class="legend"><span><i class="threat"></i>Threat only</span><span><i class="marlin"></i>Marlin on screen</span><span><i class="map"></i>Satellite view</span><span><i class="end"></i>End card</span></div>
      <div class="bignums"><div><b class="was">20 s</b><span>of drug boat before Marlin, now</span></div><div class="bigarrow">→</div><div><b>4 s</b><span>in the new cut</span></div></div>
      __FOOT__</section>''')

    # ---- 4 the film in seven beats
    beats = [
        ('0:00', 'Hook', img('hook_bow'), 'A boat is running dark for the coast.'),
        ('0:04', 'Marlin waits', img('waits_close'), 'Marlin is already out there. Waiting. Always ready.'),
        ('0:11', '01 · Detect', map_detect(), 'It detects the contact,'),
        ('0:19', '02 · Isolate', img('vector'), 'vectors the nearest Marlins in… and isolates it,'),
        ('0:31', '03 · Surveil', f'<div class="stack">{img("standoff")}<div class="inset">{img("thermal")}<span>● LIVE</span></div></div>', 'then stays on it until partners arrive.'),
        ('0:45', 'Coverage holds', map_cover(), 'Detect. Isolate. Surveil.'),
        ('0:53', 'End card', end_card(), 'Marlin.'),
    ]
    b_html = ''.join(f'''<div class="beat"><div class="beat-vis">{v}<div class="beat-time">{t}</div></div>
        <div class="beat-title">{title}</div><div class="beat-vo">“{vo}”</div></div>''' for t, title, v, vo in beats)
    pages.append(f'<section class="page"><h2>The new film in seven beats</h2><div class="beats">{b_html}</div>__FOOT__</section>')

    # ---- 5 three words
    cols = [
        ('01', 'Detect', map_detect(), img('waits_wide'), 'Contact tagged. Nearest Marlins light up.'),
        ('02', 'Isolate', map_isolate(), img('vector'), 'Several Marlins vector in and box it, at standoff.'),
        ('03', 'Surveil', map_surveil(), img('standoff'), 'Eyes on. Hold until partners make the stop.'),
    ]
    c_html = ''.join(f'''<div class="col"><div class="col-head"><span>{n}</span>{w}</div><div class="col-map">{m}</div>
        <div class="col-img">{i}</div><div class="col-cap">{cap}</div></div>''' for n, w, m, i, cap in cols)
    pages.append(f'<section class="page"><h2>Three words, each one a picture</h2><div class="cols">{c_html}</div>__FOOT__</section>')

    # ---- 6 the predator
    seq = [(img('hook_bow'), 'THREAT', 'The question: who deals with this?'),
           (img('waits_wide'), 'PREDATOR', 'The answer is already there. Calm. Ready.'),
           (img('vector'), 'THE TRAP CLOSES', 'Speed reads as a choice, not a scramble.')]
    s_html = ''.join(f'<div class="pred"><div class="pred-img">{i}</div><div class="pred-k">{k}</div><div class="pred-c">{c}</div></div>' + ('<div class="pred-arrow">→</div>' if n < 2 else '')
                     for n, (i, k, c) in enumerate(seq))
    pages.append(f'''<section class="page"><h2>Why the apex predator works</h2><div class="preds">{s_html}</div>
      <div class="guard"><b>One rule:</b> the predator is in its patience and posture. Marlin watches and tracks; partners make the stop.</div>__FOOT__</section>''')

    # ---- 7 wording
    vo = [('0:01', 'A boat is running dark for the coast.'), ('0:05', 'Marlin is already out there. Waiting. Always ready.'), ('0:12', 'It detects the contact,'),
          ('0:20', 'vectors the nearest Marlins in, fifty miles in thirty minutes,* and isolates it,'), ('0:36', 'then stays on it until partners arrive.'),
          ('0:49', 'Detect. Isolate. Surveil.'), ('0:56', 'Marlin.')]
    vo_html = ''.join(f'<div class="vo-line"><span>{t}</span><p>{l}</p></div>' for t, l in vo)
    pages.append(f'''<section class="page"><h2>Change of wording</h2><div class="word-grid">
      <div class="word-card"><div class="wc-k">TAGLINE</div><div class="strike big">Cover. Sprint. Persist.</div><div class="arrow-d">↓</div><div class="newwords big">Detect. Isolate. Surveil.</div></div>
      <div class="word-card"><div class="wc-k">ON SCREEN</div>
        <div class="chips old"><span>01 CLOSE</span><span>02 EYES ON</span><span>03 SURVEIL</span></div><div class="arrow-d">↓</div>
        <div class="chips"><span>01 DETECT</span><span>02 ISOLATE</span><span>03 SURVEIL</span></div>
        <div class="wc-k" style="margin-top:34px">ENDING</div><div class="endline"><span class="strike">engine buzz</span> → music resolves, clean</div></div>
      <div class="word-card wide"><div class="wc-k">NARRATION <small>was 20 words from 0:23 · now about 44 from 0:01</small></div>{vo_html}
        <div class="fine">*“Design target” stays on screen with this line.</div></div></div>__FOOT__</section>''')

    # ---- 8 what goes / new / to confirm
    cut = ''.join(f'<div class="thumb cut">{img(n)}<span>{l}</span></div>' for n, l in (('cut_radar', 'Aircraft radar'), ('cut_irid', 'Aircraft thermal ID'), ('cut_miss', '“Out of reach” map')))
    newv = ''.join(f'<div class="thumb new">{v}<span>{l}</span></div>' for v, l in ((img('waits_close'), 'Predator close-up'), (img('vector'), 'Marlins vectoring in'), (map_isolate(), 'Map: several Marlins box it')))
    asks = [('The three words', 'Is it <b>Detect. Isolate. Surveil.</b>?'), ('Who detects', 'Marlin itself, or a cue from another asset?'), ('The narration', 'OK to record the new lines?')]
    a_html = ''.join(f'<div class="ask"><div class="ask-n">{i + 1}</div><div><div class="ask-t">{t}</div><div class="ask-q">{q}</div></div><div class="box"></div></div>' for i, (t, q) in enumerate(asks))
    pages.append(f'''<section class="page"><h2>What goes, what is new, what we need from you</h2><div class="last">
      <div class="last-col"><div class="lc-k out">OUT</div><div class="thumbs">{cut}</div><div class="lc-k in" style="margin-top:22px">NEW</div><div class="thumbs">{newv}</div></div>
      <div class="last-col asks"><div class="lc-k">TO CONFIRM</div>{a_html}</div></div>__FOOT__</section>''')

    total = len(pages)
    pages = [p.replace('__FOOT__', footer(i + 1, total)) for i, p in enumerate(pages)]
    css = f'''
    @font-face {{ font-family: 'IBM Plex Sans'; font-weight: 400; src: url('{FONTS / "ibm-plex-sans-latin-400-normal.woff2"}'); }}
    @font-face {{ font-family: 'IBM Plex Sans'; font-weight: 600; src: url('{FONTS / "ibm-plex-sans-latin-600-normal.woff2"}'); }}
    @font-face {{ font-family: 'IBM Plex Sans'; font-weight: 700; src: url('{FONTS / "ibm-plex-sans-latin-700-normal.woff2"}'); }}
    @font-face {{ font-family: 'IBM Plex Mono'; font-weight: 400; src: url('{FONTS / "ibm-plex-mono-latin-400-normal.woff2"}'); }}
    @font-face {{ font-family: 'IBM Plex Mono'; font-weight: 500; src: url('{FONTS / "ibm-plex-mono-latin-500-normal.woff2"}'); }}
    @page {{ size: 1280px 720px; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: {NAVY}; color: {WHITE}; font-family: 'IBM Plex Sans', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .page {{ width: 1280px; height: 720px; position: relative; overflow: hidden; padding: 46px 56px 0; page-break-after: always; background: {NAVY}; }}
    h2 {{ font-size: 34px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 26px; }}
    h2 em {{ font-style: normal; color: {TEAL}; }}
    img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
    svg {{ display: block; width: 100%; height: 100%; }}
    .foot {{ position: absolute; left: 56px; right: 56px; bottom: 20px; display: flex; justify-content: space-between; font-family: 'IBM Plex Mono'; font-size: 10.5px; letter-spacing: 0.14em; color: {STEEL}; opacity: 0.8; }}
    /* cover */
    .cover {{ padding: 0; }} .cover .bg {{ position: absolute; inset: 0; }}
    .cover .shade {{ position: absolute; inset: 0; background: linear-gradient(90deg, rgba(8,15,24,0.94) 0%, rgba(8,15,24,0.78) 38%, rgba(8,15,24,0.05) 72%); }}
    .cover-text {{ position: absolute; left: 70px; top: 150px; width: 640px; }}
    .cover .logo {{ width: 200px; height: auto; margin-bottom: 44px; }}
    .kicker {{ font-family: 'IBM Plex Mono'; font-size: 14px; letter-spacing: 0.22em; color: {STEEL}; }}
    h1 {{ font-size: 92px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.02; margin: 10px 0 22px; }}
    .three {{ font-family: 'IBM Plex Mono'; font-size: 30px; letter-spacing: 0.06em; color: {TEAL}; }} .three b {{ font-weight: 500; margin-right: 14px; }}
    .sub {{ margin-top: 54px; font-size: 16px; color: {STEEL}; }}
    /* tiles */
    .wtiles {{ display: grid; grid-template-columns: 2.3fr 1fr; gap: 18px; }}
    .wtile {{ background: {PANEL}; border-radius: 14px; border: 1px solid #1d3145; height: 150px; position: relative; padding: 18px 22px; }}
    .tile-n {{ font-family: 'IBM Plex Mono'; font-size: 14px; color: {TEAL}; }}
    .wt-body {{ display: flex; align-items: center; gap: 22px; height: 62px; margin-top: 4px; }}
    .wt-cap {{ position: absolute; left: 22px; bottom: 16px; font-size: 20px; font-weight: 600; }}
    .wtile .strike {{ font-size: 18px; white-space: nowrap; }} .wtile .newwords {{ font-size: 27px; padding: 0; white-space: nowrap; }} .arrow-r {{ color: {TEAL}; font-size: 30px; }}
    .wtile .mute {{ width: 64px; height: 64px; }}
    .ptiles {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-top: 18px; }}
    .ptile {{ background: {PANEL}; border-radius: 14px; border: 1px solid #1d3145; overflow: hidden; }}
    .pt-img {{ aspect-ratio: 16/9; }}
    .pt-cap {{ padding: 14px 18px 16px; font-size: 20px; font-weight: 600; }} .pt-cap span {{ font-family: 'IBM Plex Mono'; font-size: 14px; color: {TEAL}; margin-right: 12px; font-weight: 400; }}
    .strike {{ font-family: 'IBM Plex Mono'; font-size: 14px; color: {STEEL}; text-decoration: line-through; text-decoration-color: {ORANGE}; text-decoration-thickness: 2px; }}
    .arrow-d {{ color: {TEAL}; font-size: 26px; line-height: 1; margin: 12px 0; }}
    .newwords {{ font-family: 'IBM Plex Mono'; font-size: 17px; font-weight: 500; color: {TEAL}; line-height: 1.5; padding: 0 12px; }}
    .mute {{ width: 130px; height: 130px; }}
    /* timelines */
    .tl-row {{ display: flex; align-items: flex-start; gap: 22px; margin-top: 46px; }}
    .tl-name {{ width: 74px; font-family: 'IBM Plex Mono'; font-size: 20px; font-weight: 500; letter-spacing: 0.1em; color: {STEEL}; padding-top: 22px; line-height: 1.1; }}
    .tl-name small {{ font-size: 12px; }} .tl-name.new {{ color: {TEAL}; }}
    .tl {{ flex: 1; position: relative; padding-top: 0; }}
    .tl-bar {{ display: flex; height: 70px; border-radius: 10px; overflow: hidden; gap: 2px; }}
    .seg {{ display: flex; align-items: center; justify-content: center; font-family: 'IBM Plex Mono'; font-size: 12px; letter-spacing: 0.04em; min-width: 0; }}
    .seg span {{ white-space: nowrap; overflow: hidden; padding: 0 3px; }}
    .threat {{ background: {ORANGE}; color: #2a1404; }} .marlin {{ background: {TEAL}; color: #06302c; }} .map {{ background: #24506f; color: #d9ecf7; }} .end {{ background: #2a3644; color: {STEEL}; }}
    .tl-marker {{ position: absolute; top: -34px; bottom: 22px; width: 0; border-left: 2.5px solid {WHITE}; }}
    .tl-flag {{ position: absolute; top: 0; left: 8px; white-space: nowrap; font-family: 'IBM Plex Mono'; font-size: 13px; font-weight: 500; background: {WHITE}; color: {NAVY}; padding: 3px 9px; border-radius: 4px; }}
    .tl-ticks {{ position: relative; height: 22px; margin-top: 6px; font-family: 'IBM Plex Mono'; font-size: 11px; color: {STEEL}; }}
    .tl-ticks span {{ position: absolute; transform: translateX(-50%); }} .tl-ticks span:first-child {{ transform: none; }} .tl-ticks span:last-child {{ transform: translateX(-100%); }}
    .legend {{ display: flex; gap: 30px; margin: 26px 0 0 96px; font-size: 14px; color: {STEEL}; }}
    .legend i {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 8px; vertical-align: -2px; }}
    .bignums {{ display: flex; align-items: center; gap: 44px; margin: 44px 0 0 96px; }}
    .bignums b {{ display: block; font-size: 82px; font-weight: 700; line-height: 1; color: {TEAL}; }} .bignums b.was {{ color: {ORANGE}; }}
    .bignums span {{ font-size: 16px; color: {STEEL}; }} .bigarrow {{ font-size: 60px; color: {STEEL}; }}
    /* seven beats */
    .beats {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 18px 16px; }}
    .beat {{ width: 280px; }}
    .beat-vis {{ position: relative; aspect-ratio: 16/9; border-radius: 10px; overflow: hidden; background: {PANEL}; border: 1px solid #1d3145; }}
    .beat-time {{ position: absolute; left: 8px; top: 8px; font-family: 'IBM Plex Mono'; font-size: 13px; font-weight: 500; background: rgba(8,15,24,0.82); padding: 3px 8px; border-radius: 4px; }}
    .beat-title {{ margin-top: 10px; font-size: 19px; font-weight: 700; }}
    .beat-vo {{ margin-top: 3px; font-size: 13.5px; color: {STEEL}; font-style: italic; line-height: 1.32; }}
    .beat:nth-child(3) .beat-title, .beat:nth-child(4) .beat-title, .beat:nth-child(5) .beat-title {{ color: {TEAL}; }}
    .stack {{ position: relative; width: 100%; height: 100%; }}
    .inset {{ position: absolute; right: 8px; top: 8px; width: 38%; aspect-ratio: 16/9; border: 1.5px solid rgba(255,255,255,0.8); border-radius: 3px; overflow: hidden; }}
    .inset span {{ position: absolute; left: 5px; bottom: 3px; font-family: 'IBM Plex Mono'; font-size: 8.5px; color: {TEAL}; }}
    .endcard {{ width: 100%; height: 100%; background: {PANEL}; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .endcard img {{ height: auto; }} .ec-name {{ font-weight: 700; letter-spacing: 0.3em; padding-left: 0.3em; margin-top: 10px; }}
    .ec-tag {{ font-family: 'IBM Plex Mono'; letter-spacing: 0.1em; margin-top: 4px; }} .ec-rule {{ width: 44px; height: 2px; background: {ORANGE}; margin-top: 12px; }}
    /* three words */
    .cols {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }}
    .col-head {{ font-family: 'IBM Plex Mono'; font-size: 34px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 12px; }}
    .col-head span {{ color: {TEAL}; font-size: 20px; margin-right: 12px; }}
    .col-map, .col-img {{ aspect-ratio: 16/9; border-radius: 10px; overflow: hidden; border: 1px solid #1d3145; }} .col-img {{ margin-top: 12px; }}
    .col-cap {{ margin-top: 12px; font-size: 16px; color: {WHITE}; }}
    /* predator */
    .preds {{ display: flex; align-items: flex-start; gap: 8px; margin-top: 10px; }}
    .pred {{ flex: 1; }} .pred-img {{ aspect-ratio: 16/10.5; border-radius: 12px; overflow: hidden; border: 1px solid #1d3145; }}
    .pred-k {{ font-family: 'IBM Plex Mono'; font-size: 15px; letter-spacing: 0.18em; color: {TEAL}; margin-top: 18px; }}
    .pred-c {{ font-size: 23px; font-weight: 600; line-height: 1.25; margin-top: 6px; }}
    .pred-arrow {{ font-size: 40px; color: {STEEL}; padding-top: 96px; }}
    .guard {{ margin-top: 40px; padding: 18px 24px; border-left: 4px solid {ORANGE}; background: {PANEL}; border-radius: 0 10px 10px 0; font-size: 18px; color: {WHITE}; }}
    .guard b {{ color: {ORANGE}; }}
    /* wording */
    .word-grid {{ display: grid; grid-template-columns: 300px 300px 1fr; gap: 18px; }}
    .word-card {{ background: {PANEL}; border: 1px solid #1d3145; border-radius: 14px; padding: 24px 22px; height: 500px; }}
    .wc-k {{ font-family: 'IBM Plex Mono'; font-size: 12.5px; letter-spacing: 0.2em; color: {STEEL}; margin-bottom: 26px; }}
    .wc-k small {{ letter-spacing: 0.04em; opacity: 0.85; margin-left: 10px; }}
    .strike.big {{ font-size: 19px; }} .newwords.big {{ font-size: 30px; padding: 0; line-height: 1.35; }}
    .chips {{ display: flex; flex-direction: column; gap: 8px; }} .chips span {{ font-family: 'IBM Plex Mono'; font-size: 17px; letter-spacing: 0.12em; border: 1.5px solid {TEAL}; color: {TEAL}; border-radius: 5px; padding: 6px 12px; width: fit-content; }}
    .chips.old span {{ border-color: #3b4c5e; color: {STEEL}; text-decoration: line-through; text-decoration-color: {ORANGE}; font-size: 14px; padding: 4px 10px; }}
    .endline {{ font-size: 16px; }} .endline .strike {{ font-size: 15px; }}
    .vo-line {{ display: flex; gap: 16px; align-items: baseline; padding: 9px 0; border-top: 1px solid #1d3145; }}
    .vo-line span {{ font-family: 'IBM Plex Mono'; font-size: 14px; color: {TEAL}; width: 44px; flex: none; }}
    .vo-line p {{ font-size: 19px; line-height: 1.3; }}
    .fine {{ margin-top: 14px; font-size: 12.5px; color: {STEEL}; }}
    /* last page */
    .last {{ display: grid; grid-template-columns: 1.55fr 1fr; gap: 34px; }}
    .lc-k {{ font-family: 'IBM Plex Mono'; font-size: 13px; letter-spacing: 0.22em; color: {STEEL}; margin-bottom: 12px; }} .lc-k.out {{ color: {ORANGE}; }} .lc-k.in {{ color: {TEAL}; }}
    .thumbs {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .thumb {{ position: relative; }} .thumb img, .thumb svg {{ aspect-ratio: 16/9; height: auto; border-radius: 8px; border: 1px solid #1d3145; }}
    .thumb span {{ display: block; margin-top: 7px; font-size: 14.5px; font-weight: 600; }}
    .thumb.cut img {{ opacity: 0.8; border: 1.5px solid {ORANGE}; }}
    .thumb.cut::after {{ content: 'OUT'; position: absolute; right: 8px; top: 8px; font-family: 'IBM Plex Mono'; font-size: 11px; letter-spacing: 0.14em; background: {ORANGE}; color: #2a1404; padding: 2px 7px; border-radius: 3px; }}
    .thumb.new::after {{ content: 'NEW'; position: absolute; right: 8px; top: 8px; font-family: 'IBM Plex Mono'; font-size: 11px; letter-spacing: 0.14em; background: {TEAL}; color: #06302c; padding: 2px 7px; border-radius: 3px; }}
    .thumb.new img, .thumb.new svg {{ border: 1.5px solid {TEAL}; }}
    .ask {{ display: flex; align-items: center; gap: 16px; background: {PANEL}; border: 1px solid #1d3145; border-radius: 12px; padding: 20px 18px; margin-bottom: 14px; }}
    .ask-n {{ font-family: 'IBM Plex Mono'; font-size: 26px; color: {TEAL}; width: 30px; }}
    .ask-t {{ font-family: 'IBM Plex Mono'; font-size: 12.5px; letter-spacing: 0.18em; color: {STEEL}; text-transform: uppercase; }}
    .ask-q {{ font-size: 19px; font-weight: 600; margin-top: 5px; line-height: 1.25; }} .ask-q b {{ color: {TEAL}; }}
    .box {{ margin-left: auto; width: 30px; height: 30px; border: 2px solid {STEEL}; border-radius: 6px; flex: none; }}
    '''
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>Marlin · New structure</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
    (HERE / 'index.html').write_text(html)
    js = f'''
    const {{chromium}} = require('playwright');
    (async () => {{
      const b = await chromium.launch(); const p = await b.newPage({{viewport: {{width: 1280, height: 720}}}});
      await p.goto('file://{HERE / "index.html"}'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
      await p.pdf({{path: '{HERE / "Marlin_New_Structure.pdf"}', width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true}});
      await b.close();
    }})();'''
    subprocess.run(['node', '-e', js], check=True, cwd=str(ROOT))
    print('wrote', HERE / 'Marlin_New_Structure.pdf', 'pages:', total)


if __name__ == '__main__':
    build()
