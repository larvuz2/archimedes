#!/usr/bin/env bash
# Animatic v4.0 hand-off files: clean 3D plates of the new shots (for the video model) and the audio stems.
# Usage: scripts/export_v4.sh   (after the plates are rendered and scripts/build_audio_v4.py has run)
set -euo pipefail
cd "$(dirname "$0")/.."
REF=review/v4/reference; AUD=review/v4/audio
mkdir -p "$REF" "$AUD"
plate() { cp "public/blender/$1.mp4" "$REF/$2_plate.mp4"; }
plate shot06b  marlin-waits_predator-close-up
plate shots1   detect_sensor-sweeps-and-stops
plate shotf1   detect_fan-comes-alive
plate shotk1   isolate_strut-slicing-the-surface
plate shotv1   isolate_three-marlins-vectoring-in
plate shotr2   isolate_head-on
plate shott1   isolate_top-down
plate shoti1   isolate_taking-station_from-above
plate shot10h  surveil_standoff-hold
# Stems at their level in the mix (-8.4 dB = bus trim + master gain), before the master's level ride and limiter.
for n in music sfx vo; do
  ffmpeg -v error -y -i "public/audio/v4/$n.wav" -af "volume=-8.4dB" -c:a flac -sample_fmt s16 "$AUD/marlin-v4.0_stem_$n.flac"
done
ffmpeg -v error -y -i public/audio/v4/mix.flac -c:a pcm_s16le "$AUD/marlin-v4.0_mix.wav"
ls -la "$REF" "$AUD"
