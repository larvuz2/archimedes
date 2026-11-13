#!/usr/bin/env bash
# Render every 3D shot of Storyboard V5 with Blender (Cycles, CPU) and encode review/reference clips.
# Resumable: frames that already exist are skipped. Usage: blender/render_all.sh [RES] [SAMPLES]
set -uo pipefail
cd "$(dirname "$0")/.."
RES="${1:-1280x720}"; SAMPLES="${2:-8}"
PY=/opt/venv-blender/bin/python
OUT=blender/out
mkdir -p "$OUT" public/blender blender/scenes
render() {  # shot [--ir]
  local tag="shot$1"; [ "${2:-}" = "--ir" ] && [ "$1" != "03" ] && tag="shot$1_ir"
  echo "=== $tag $(date +%H:%M:%S)"
  $PY blender/previz.py --shot "$1" ${2:-} --res "$RES" --samples "$SAMPLES" --out "$OUT" --save-blend blender/scenes 2>&1 \
    | grep -E "^RENDER .* frame [0-9]*0/|^DONE|Error|Traceback" 
  local first; first=$(ls "$OUT/$tag"/*.jpg | head -1 | xargs basename | sed 's/.jpg//' | sed 's/^0*//')
  ffmpeg -v error -y -framerate 24 -start_number "$first" -i "$OUT/$tag/%04d.jpg" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p \
    -movflags +faststart "public/blender/$tag.mp4" && echo "encoded public/blender/$tag.mp4 (first frame $first)"
  [ -f "$OUT/$tag/tracks.json" ] && cp "$OUT/$tag/tracks.json" "public/blender/$tag.tracks.json"
}
render 01
render 03
render 06
render 07
render 10 --ir
render 10
render 09
echo "ALL DONE $(date +%H:%M:%S)"
