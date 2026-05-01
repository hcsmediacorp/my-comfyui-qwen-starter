#!/bin/bash
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-./ComfyUI}"
PORT="${PORT:-7860}"

cd "${COMFY_DIR}"

# Optional: Modell-Dateien via Secret HF_TOKEN beim Start herunterladen
python3 ../app.py

# ComfyUI starten (HF Spaces erwartet Port 7860)
python3 main.py --listen 0.0.0.0 --port "${PORT}"
