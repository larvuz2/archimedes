"""Crop the 11 navy sketch panels out of the storyboard PDF as shot-NN.png.

Usage:
  pdftoppm -r 300 -png docs/reference/Storyboard_V3.pdf <pages_dir>/p
  python3 scripts/extract_storyboard_frames.py <pages_dir> docs/reference/frames

Panels split across a page break are stitched back together.
"""
import sys, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

pages, out = map(pathlib.Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
NAVY = (18, 32, 46)

panels = []  # dicts in reading order
for pi, page in enumerate(sorted(pages.glob('p-*.png'), key=lambda p: int(p.stem.split('-')[1]))):
    im = np.asarray(Image.open(page).convert('RGB'))
    d = np.abs(im.astype(int) - NAVY).max(axis=2)
    mask = ndimage.binary_closing(d < 14, iterations=6)
    lab, _ = ndimage.label(mask)
    found = []
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if x1 - x0 < 600 or y1 - y0 < 60:
            continue
        found.append(dict(page=pi, x=x0, y0=y0, y1=y1, h=im.shape[0], img=im[sl]))
    found.sort(key=lambda f: (f['y0'], f['x']))
    for f in found:
        # continuation of a panel cut at the bottom of the previous page?
        prev = next((p for p in panels if p['page'] == pi - 1 and p['x'] == f['x']
                     and p['y1'] > p['h'] - 400 and f['y0'] < 400 and not p.get('joined')), None)
        if prev is not None:
            prev['img'] = np.vstack([prev['img'], f['img']])
            prev['joined'] = True
        else:
            panels.append(f)

# Reading order within a page is row-major; the PDF lays shots out in 2 columns.
for i, p in enumerate(panels, 1):
    Image.fromarray(p['img']).save(out / f'shot-{i:02d}.png')
    print(f'shot-{i:02d}.png  {p["img"].shape[1]}x{p["img"].shape[0]}')
print(len(panels), 'panels')
