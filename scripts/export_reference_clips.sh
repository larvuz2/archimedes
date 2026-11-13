#!/usr/bin/env bash
# Export per-shot reference clips for the video model / client review.
#   *_plate.mp4  = the clean Blender render of a 3D shot (no graphics, no slate): camera move + blocking
#   *_comp.mp4   = the shot as it appears in the animatic, without the review slate (graphics included)
# Usage: scripts/export_reference_clips.sh   (renders a slate-free pass of the edit first)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=review/v3/reference
mkdir -p "$OUT"
CLEAN=out/marlin-v3-noslate.mp4
mkdir -p out
npx remotion render src/index.ts Marlin "$CLEAN" --props='{"slate":false}' --crf=16 >/dev/null
cut() {  # name start end
  ffmpeg -v error -y -ss "$2" -i "$CLEAN" -t "$(python3 -c "print($3-$2)")" -an -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT/$1_comp.mp4"
}
cut shot01_the-boat 0 4
cut shot02_aircraft-radar 4 7
cut shot03_infrared-id 7 10
cut shot04_out-of-reach 10 16
cut shot05_on-station 16 20
cut shot06_loiter 20 23
cut shot07_lift 23 28
cut shot08_converge 28 34
cut shot09_the-run 34 40
cut shot10_eyes-on 40 46
cut shot11_the-fleet 46 56
cut shot12_end-card 56 60
plate() { cp "public/blender/$1.mp4" "$OUT/$2_plate.mp4"; }
plate shot01 shot01_the-boat
plate shot03 shot03_infrared-id_thermal
plate shot06 shot06_loiter
plate shot07 shot07_lift
plate shot09 shot09_the-run
plate shot10_ir shot10_eyes-on_thermal
plate shot10 shot10_eyes-on_standoff
ls -la "$OUT"
