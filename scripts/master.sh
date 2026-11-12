#!/usr/bin/env bash
# Render the current cut and master its audio (-14 LUFS, -1.5 dBTP) without re-encoding the picture.
# Usage: scripts/master.sh review/marlin-animatic-v2.0.mp4
set -euo pipefail
out="$1"; raw="${out%.mp4}.raw.mp4"
npx remotion render src/index.ts Marlin "$raw" --crf=20
ffmpeg -v error -y -i "$raw" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k "$out"
rm -f "$raw"
echo "mastered -> $out"
