# SHWTY Report

RESOLVED: Mutually exclusive argument conflict (--lowvram vs --cpu).

## Changes Applied
- Replaced `--lowvram` with `--novram` in startup command.
- Added `--disable-smart-memory` for stricter CPU behavior.
- Added tee-based logging to `/root/comfy/ComfyUI/shwty_debug.log`.

## Current Startup Command
`python3 main.py --cpu --novram --listen 0.0.0.0 --port 7860 --disable-smart-memory --preview-method auto`
