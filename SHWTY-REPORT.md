# SHWTY Report

RESOLVED: Mutually exclusive argument conflict (--lowvram vs --cpu).

## Last Ritual
Updated startup command to strict CPU-only flags:
`python main.py --cpu --listen 0.0.0.0 --port 7860 --disable-smart-memory --preview-method auto`

## Gnosis Failure
No fresh crash tail captured in this commit cycle; awaiting next runtime log tail from `/root/comfy/ComfyUI/shwty_debug.log`.

## Proposed Fix
If next failure is:
- `ModuleNotFoundError` → install missing package in build
- argument conflict → strip incompatible flags
- memory-related → reduce model pressure (quantization/resolution/steps)
