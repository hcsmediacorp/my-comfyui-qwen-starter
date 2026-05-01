import os
from pathlib import Path
from huggingface_hub import hf_hub_download

BASE = Path('/workspace/ComfyUI/models')
TARGETS = {
    'diffusion_models': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', 'Q4_K_M.gguf'),
    ],
    'text_encoders': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', 'qwen2.5-vl-7b-edit-q4_0.gguf'),
    ],
    'vae': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', 'pig_qwen_image_vae_fp32-f16.gguf'),
    ],
    'loras': [
        # CPU-effizienter 4-step Adapter (anpassbar)
        ('ByteDance/Hyper-SD', 'Hyper-SD15-4steps-lora.safetensors'),
    ],
}


def ensure_dirs():
    for sub in TARGETS:
        (BASE / sub).mkdir(parents=True, exist_ok=True)


def maybe_download():
    token = os.getenv('HF_TOKEN')
    if not token:
        print('HF_TOKEN not set; skipping model download at startup.')
        return

    for sub, files in TARGETS.items():
        for repo_id, filename in files:
            dest = BASE / sub
            target_path = dest / filename
            if target_path.exists():
                print(f'Exists, skip: {target_path}')
                continue
            print(f'Downloading {repo_id}/{filename} -> {dest}')
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                token=token,
                local_dir=str(dest),
                local_dir_use_symlinks=False,
            )


if __name__ == '__main__':
    ensure_dirs()
    maybe_download()
