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

# ComfyUI API im Hintergrund starten (UI wird über Gradio bereitgestellt)
# NOTE: --lowvram conflicts with --cpu in this ComfyUI build (Exit Code 2),
# so we use CPU-safe memory pressure reduction flags.
python3 main.py --cpu --listen 127.0.0.1 --port 8188 --disable-smart-memory --preview-method auto --cache-lru 1 2>&1 | tee -a "${LOG_FILE}" &

# Responsive Web-UI starten (Port 7860)
python3 /webui.py 2>&1 | tee -a "${LOG_FILE}"
