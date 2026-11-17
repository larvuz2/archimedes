#!/usr/bin/env bash
# Animatic v5.0 (Storyboard V7): the new 3D shots for Act 3 "The stop". Resumable.
# Usage: blender/render_v5.sh [RES] [SAMPLES]
set -uo pipefail
cd "$(dirname "$0")/.."
RES="${1:-1280x720}"; SAMPLES="${2:-8}"
PY=/opt/venv-blender/bin/python; OUT=blender/out
mkdir -p "$OUT" public/blender blender/scenes
render() {  # shot-id
  local tag="shot$1"
  echo "=== $tag $(date +%H:%M:%S)"
  $PY blender/previz.py --shot "$1" --res "$RES" --samples "$SAMPLES" --out "$OUT" --save-blend blender/scenes 2>&1 | grep -E "^DONE|Error|Traceback|t_foul"
  ffmpeg -v error -y -framerate 24 -start_number 1 -i "$OUT/$tag/%04d.jpg" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -movflags +faststart "public/blender/$tag.mp4" \
    && echo "encoded public/blender/$tag.mp4"
  [ -f "$OUT/$tag/tracks.json" ] && cp "$OUT/$tag/tracks.json" "public/blender/$tag.tracks.json"
}
render x1   # 11 fouled
render n1   # 10 net away
render p1   # 09 pass
render h1   # 12 hold
render u1   # 11 underwater cutaway
echo "ALL DONE $(date +%H:%M:%S)"
