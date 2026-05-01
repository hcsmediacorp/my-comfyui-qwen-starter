import os, json, random, time
from pathlib import Path
import requests
import gradio as gr

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
INPUT_DIR = Path("/workspace/ComfyUI/input")
INPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_prompt_payload(user_prompt: str, seed: int, steps: int, cfg: float, sampler: str, scheduler: str):
    ckpt = os.getenv("QWEN_DIFFUSION_FILE", "qwen-image-edit-2511-Q2_K.gguf")
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": user_prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "artifacts, blurry, distorted", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 768, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg), "sampler_name": sampler, "scheduler": scheduler, "denoise": 1, "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "shwty_qwen", "images": ["6", 0]}}
    }


def simplify_error(status_code: int, text: str):
    try:
        data = json.loads(text)
        err = data.get("error", {})
        typ = err.get("type", "unknown")
        msg = err.get("message", "")
        return f"[SYSTEM FAILURE] {typ} - {msg} - Suggested Fix: check RECOVERY_PROTOCOL.md"
    except Exception:
        return f"[SYSTEM FAILURE] HTTP {status_code}: {text[:180]}"


def run_edit(image, prompt, adv_enabled, steps, cfg, sampler, scheduler, seed_val, randomize_seed):
    if image is None:
        return None, "Bitte ein Bild hochladen.", 0
    if not prompt or not prompt.strip():
        return None, "Bitte einen Prompt eingeben.", 0

    if adv_enabled:
        run_steps, run_cfg, run_sampler, run_scheduler = int(steps), float(cfg), sampler, scheduler
        seed = random.randint(1, 2_147_483_647) if randomize_seed else int(seed_val)
    else:
        run_steps, run_cfg, run_sampler, run_scheduler = 4, 1.1, "euler", "simple"
        seed = random.randint(1, 2_147_483_647)

    ts = int(time.time())
    image.save(INPUT_DIR / f"shwty_input_{ts}.png")

    payload = {"prompt": build_prompt_payload(prompt.strip(), seed, run_steps, run_cfg, run_sampler, run_scheduler)}

    try:
        r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
        if r.status_code >= 300:
            return None, simplify_error(r.status_code, r.text), 0
    except Exception as e:
        return None, f"[SYSTEM FAILURE] bridge_offline - {e} - Suggested Fix: verify Comfy API", 0

    for p in (15, 40, 70, 100):
        time.sleep(0.2)
    return image, f"GNOSIS CONNECTED | Seed={seed} Steps={run_steps} CFG={run_cfg}", 100


css = """
body { background:#000 !important; color:#d7ffe8 !important; font-family:monospace !important; }
.gradio-container { max-width: 980px !important; margin: 0 auto; }
button { border:1px solid #00f5ff !important; color:#00f5ff !important; }
"""

with gr.Blocks(css=css, title="SHWTY Image Edit Studio") as demo:
    gr.Markdown("# SHWTY Image Edit Studio\n### DECRYPTING REALITY...")

    with gr.Row():
        with gr.Column():
            inp = gr.Image(type="pil", label="Upload Image")
            pr = gr.Textbox(label="Prompt", lines=3)
            adv = gr.Checkbox(label="Advanced aktivieren", value=False)
            run = gr.Button("Generate / Edit")
        with gr.Column():
            out = gr.Image(label="Output Preview")
            status = gr.Textbox(label="Status Terminal", interactive=False)
            prog = gr.Slider(0, 100, value=0, step=1, label="REVEALING REALITY", interactive=False)

    with gr.Accordion("Advanced Settings", open=False):
        steps = gr.Slider(1, 50, value=4, step=1, label="Steps")
        cfg = gr.Slider(0.0, 10.0, value=1.1, step=0.1, label="CFG")
        sampler = gr.Dropdown(["euler", "dpmpp_2m"], value="euler", label="Sampler")
        scheduler = gr.Dropdown(["simple", "karras"], value="simple", label="Scheduler")
        seed_val = gr.Number(value=12345, label="Seed")
        rand = gr.Checkbox(value=True, label="Randomize Seed")

    run.click(run_edit, [inp, pr, adv, steps, cfg, sampler, scheduler, seed_val, rand], [out, status, prog])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
