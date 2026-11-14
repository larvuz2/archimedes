#!/usr/bin/env bash
# v4 extra: the standoff hold (continues shot 10 past its last frame). Usage: blender/render_v4b.sh [RES] [SAMPLES]
set -uo pipefail
cd "$(dirname "$0")/.."
RES="${1:-1280x720}"; SAMPLES="${2:-8}"
PY=/opt/venv-blender/bin/python; OUT=blender/out
echo "=== shot10h $(date +%H:%M:%S)"
$PY blender/previz.py --shot 10h --res "$RES" --samples "$SAMPLES" --out "$OUT" 2>&1 | grep -E "^DONE|Error|Traceback"
ffmpeg -v error -y -framerate 24 -start_number 145 -i "$OUT/shot10h/%04d.jpg" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -movflags +faststart public/blender/shot10h.mp4 \
  && echo "encoded public/blender/shot10h.mp4"
echo "ALL DONE B $(date +%H:%M:%S)"
