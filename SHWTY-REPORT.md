# SHWTY Report

## Last Ritual
- Reworked Gradio bridge payload to strict Comfy node-map (`class_type` + `inputs`).
- Added functional Advanced mappings: Steps, CFG, Sampler, Scheduler, Seed, Randomize toggle.
- Added CPU-stable defaults (768x768 latent, steps=4, cfg=1.1).

## Memory Benchmarks (CPU target)
- Default mode: 4 steps, cfg 1.1, 768x768, random seed.
- Expected lower RAM pressure vs prior 1024x1024 baseline.

## Advanced Tab Mapping (confirmed)
- Steps slider -> KSampler.steps
- CFG slider -> KSampler.cfg
- Sampler dropdown -> KSampler.sampler_name
- Scheduler dropdown -> KSampler.scheduler
- Seed + Randomize -> KSampler.seed

## Gnosis Failure (last known)
- 400 `missing_node_type` from malformed workflow payload (resolved).

## Proposed Fix (next if MemoryError appears)
- Reduce latent to 640x640 then 512x512.
- Reduce steps to 2–3.
- Keep Q2_K diffusion file and random seed.
