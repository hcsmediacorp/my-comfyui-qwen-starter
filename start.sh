#!/bin/bash
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-/workspace/ComfyUI}"
PORT="${PORT:-7860}"

cd "${COMFY_DIR}"

# Optional: Modell-Dateien via Secret HF_TOKEN beim Start herunterladen
python3 /app.py

# Vollständiges Startup-Logging (Konsole + Datei)
mkdir -p /root/comfy/ComfyUI
LOG_FILE="/root/comfy/ComfyUI/shwty_debug.log"

# ComfyUI starten (CPU-only, ohne VRAM-Flags)
python3 main.py --cpu --listen 0.0.0.0 --port "${PORT}" --disable-smart-memory --preview-method auto 2>&1 | tee -a "${LOG_FILE}"
