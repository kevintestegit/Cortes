#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v apt-get >/dev/null 2>&1; then
  echo "Instale dependencias de sistema se ainda nao fez:"
  echo "  sudo apt install ffmpeg python3-tk"
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r requirements-optional.txt

echo "Setup concluido. Rode: ./scripts/run_gui_linux.sh"
