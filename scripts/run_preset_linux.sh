#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ $# -lt 1 ]]; then
  echo "Uso: ./scripts/run_preset_linux.sh input/video.mp4 [preset] [max_shorts]"
  exit 1
fi

INPUT_VIDEO="$1"
PRESET="${2:-funny}"
MAX_SHORTS="${3:-5}"

exec .venv/bin/python -m src.main \
  --input "$INPUT_VIDEO" \
  --preset "$PRESET" \
  --max-shorts "$MAX_SHORTS"
