import os
from pathlib import Path
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError, RemoteEntryNotFoundError

COMFY_DIR = Path(os.getenv('COMFY_DIR', './ComfyUI'))
BASE = COMFY_DIR / 'models'
TARGETS = {
    'diffusion_models': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', os.getenv('QWEN_DIFFUSION_FILE', 'qwen-image-edit-2511-Q2_K.gguf')),
    ],
    'text_encoders': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', 'qwen2.5-vl-7b-edit-q4_0.gguf'),
    ],
    'vae': [
        ('unsloth/Qwen-Image-Edit-2511-GGUF', 'pig_qwen_image_vae_fp32-f16.gguf'),
    ],
    'loras': [
        # Verifiziertes Lightning-LoRA Repo
        ('lightx2v/Qwen-Image-Edit-2511-Lightning', os.getenv('QWEN_LIGHTNING_LORA_FILE', 'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors')),
    ],
}


def ensure_dirs():
    for sub in TARGETS:
        (BASE / sub).mkdir(parents=True, exist_ok=True)


def maybe_download():
    if os.getenv('SKIP_MODEL_DOWNLOAD', '0') == '1':
        print('SKIP_MODEL_DOWNLOAD=1; skipping model download.')
        return

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
            try:
                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    token=token,
                    local_dir=str(dest),
                )
            except (RemoteEntryNotFoundError, HfHubHTTPError) as e:
                print(f'WARN: could not download {repo_id}/{filename}: {e}')
                print('Continuing startup. Set correct file names via env vars if needed.')
            except Exception as e:
                print(f'WARN: unexpected download error for {repo_id}/{filename}: {e}')
                print('Continuing startup.')


if __name__ == '__main__':
    ensure_dirs()
    maybe_download()
