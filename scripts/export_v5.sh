#!/usr/bin/env bash
# Animatic v5.0 hand-off files: clean 3D plates of the new shots (for the video model) and the audio stems.
# Usage: scripts/export_v5.sh   (after blender/render_v5.sh and scripts/build_audio_v5.py)
set -euo pipefail
cd "$(dirname "$0")/.."
REF=review/v5/reference; AUD=review/v5/audio
mkdir -p "$REF" "$AUD"
plate() { cp "public/blender/$1.mp4" "$REF/$2_plate.mp4"; }
plate shotp1 09_pass_overhead
plate shotn1 10_net-away_overhead
plate shotx1 11_fouled_swerve-into-the-net
plate shotu1 11_fouled_underwater-prop-cutaway
plate shoth1 12_hold_partner-closing
# stems at their level in the mix, before the master (glue compression, limiter)
for n in music sfx vo; do
  ffmpeg -v error -y -i "public/audio/v5/$n.wav" -af "volume=-8.3dB" -c:a flac -sample_fmt s16 "$AUD/marlin-v5.0_stem_$n.flac"
done
ffmpeg -v error -y -i public/audio/v5/mix.flac -c:a pcm_s16le "$AUD/marlin-v5.0_mix.wav"
ls -la "$REF" "$AUD"
