# RECOVERY_PROTOCOL.md

## Phase 1 — Isolate
- `ModuleNotFoundError` → missing dependency.
- `ArgumentError` / `Exit code 2` → conflicting CLI flags.
- `MemoryError` / OOM / killed → memory pressure.

## Phase 2 — Neutralize
- ModuleNotFoundError: add/install dependency in `requirements.txt` and Docker build.
- ArgumentError: remove conflicting flags; in CPU-only mode keep `--cpu` and avoid VRAM flags.
- MemoryError: lower quantization, reduce resolution/steps, enable stricter CPU-friendly settings.

## Phase 3 — Verify
- Commit minimal patch.
- Push to GitHub + Hugging Face Space.
- Re-check runtime + logs and iterate.
