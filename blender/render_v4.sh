#!/usr/bin/env bash
# Render the extra v4 shots (predator close-up, Marlins vectoring in, isolate aerial and beat-length cutaways).
# Resumable. Usage: blender/render_v4.sh [RES] [SAMPLES]
set -uo pipefail
cd "$(dirname "$0")/.."
RES="${1:-1280x720}"; SAMPLES="${2:-8}"
PY=/opt/venv-blender/bin/python; OUT=blender/out
mkdir -p "$OUT" public/blender blender/scenes
render() {  # shot-id [frames]
  local tag="shot$1"
  echo "=== $tag $(date +%H:%M:%S)"
  $PY blender/previz.py --shot "$1" ${2:+--frames $2} --res "$RES" --samples "$SAMPLES" --out "$OUT" --save-blend blender/scenes 2>&1 | grep -E "^DONE|Error|Traceback"
  ffmpeg -v error -y -framerate 24 -start_number 1 -i "$OUT/$tag/%04d.jpg" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -movflags +faststart "public/blender/$tag.mp4" \
    && echo "encoded public/blender/$tag.mp4"
}
render 06b 1-84
render v1
render i1
render f1
render k1
render r2
render t1
render s1
echo "ALL DONE $(date +%H:%M:%S)"
