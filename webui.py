import os, json, random, time, threading
from pathlib import Path
import requests
import websocket
import gradio as gr

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
WS_URL = COMFY_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
INPUT_DIR = Path("/workspace/ComfyUI/input")
INPUT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS = {"value": 0, "text": "Bereit"}


def ws_listener():
    while True:
        try:
            ws = websocket.create_connection(WS_URL, timeout=30)
            while True:
                data = json.loads(ws.recv())
                t, d = data.get("type"), data.get("data", {})
                if t == "progress":
                    v = int(d.get("value", 0)); m = max(int(d.get("max", 1) or 1), 1)
                    PROGRESS["value"] = int((v / m) * 100)
                    PROGRESS["text"] = f"Generierung läuft: Schritt {v}/{m}"
                elif t == "execution_success":
                    PROGRESS["value"] = 100; PROGRESS["text"] = "Fertig"
        except Exception:
            PROGRESS["text"] = "Verbindung wird neu aufgebaut …"
            time.sleep(2)


def get_object_info():
    try:
        r = requests.get(f"{COMFY_URL}/object_info", timeout=15)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}


def available_checkpoints(object_info):
    info = object_info.get("CheckpointLoaderSimple", {})
    req = info.get("input", {}).get("required", {})
    ckpt_meta = req.get("ckpt_name", [])
    if ckpt_meta and isinstance(ckpt_meta[0], list):
        return ckpt_meta[0]
    return []


def build_prompt_payload(prompt_text, seed, steps, cfg, sampler, scheduler, ckpt_name):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt_name}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "blur, artifacts, distortion", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 768, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {"seed": int(seed), "steps": int(steps), "cfg": float(cfg), "sampler_name": sampler, "scheduler": scheduler, "denoise": 1, "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "shwty_qwen", "images": ["6", 0]}},
    }


def parse_error(status_code, text):
    try:
        d = json.loads(text)
        err = d.get("error", {})
        return f"Fehler: {err.get('type','unknown')} – {err.get('message','Unbekannt')}"
    except Exception:
        return f"Fehler: HTTP {status_code}"


def run_edit(image, prompt, adv_enabled, steps, cfg, sampler, scheduler, seed_val, randomize_seed):
    if image is None:
        return None, "Bitte lade ein Bild hoch.", 0
    if not (prompt or "").strip():
        return None, "Bitte gib einen Prompt ein.", 0

    obj = get_object_info()
    ckpts = available_checkpoints(obj)
    if not ckpts:
        return None, "Kein kompatibles Checkpoint-Modell in ComfyUI gefunden. Bitte ein Modell in models/checkpoints bereitstellen.", 0

    preferred = os.getenv("QWEN_DIFFUSION_FILE", "")
    ckpt = preferred if preferred in ckpts else ckpts[0]

    if adv_enabled:
        run_steps, run_cfg = int(steps), float(cfg)
        run_sampler, run_scheduler = sampler, scheduler
        seed = random.randint(1, 2_147_483_647) if randomize_seed else int(seed_val)
    else:
        run_steps, run_cfg, run_sampler, run_scheduler = 4, 1.1, "euler", "simple"
        seed = random.randint(1, 2_147_483_647)

    image.save(INPUT_DIR / f"input_{int(time.time())}.png")
    payload = {"prompt": build_prompt_payload(prompt.strip(), seed, run_steps, run_cfg, run_sampler, run_scheduler, ckpt)}

    try:
        PROGRESS["value"] = 1
        PROGRESS["text"] = "Auftrag wird gesendet …"
        r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
        if r.status_code >= 300:
            return None, parse_error(r.status_code, r.text), 0
    except Exception as e:
        return None, f"ComfyUI nicht erreichbar: {e}", 0

    return image, f"Auftrag gestartet. Modell: {ckpt} | Seed: {seed}", PROGRESS["value"]


def poll_progress():
    return PROGRESS["text"], PROGRESS["value"]

css = ":root{--bg:#f7f9fc;--text:#1f2937;} body{background:var(--bg)!important;color:var(--text)!important;} .gradio-container{max-width:1060px!important;margin:0 auto;}"

with gr.Blocks(title="SHWTY Image Edit Studio") as demo:
    gr.Markdown("# SHWTY Image Edit Studio (v1 Beta)\nEinfache Bildbearbeitung mit stabilen CPU-Defaults.")
    with gr.Row():
        with gr.Column():
            inp = gr.Image(type="pil", label="1) Bild hochladen")
            pr = gr.Textbox(label="2) Prompt", lines=3)
            adv = gr.Checkbox(label="Erweiterte Einstellungen aktivieren", value=False)
            run = gr.Button("3) Generieren", variant="primary")
        with gr.Column():
            out = gr.Image(label="Ausgabe")
            status = gr.Textbox(label="Status", interactive=False)
            prog = gr.Slider(0, 100, value=0, step=1, label="Fortschritt", interactive=False)

    with gr.Accordion("Erweiterte Einstellungen", open=False):
        steps = gr.Slider(1, 50, value=4, step=1, label="Steps")
        cfg = gr.Slider(0.0, 10.0, value=1.1, step=0.1, label="CFG")
        sampler = gr.Dropdown(["euler", "dpmpp_2m"], value="euler", label="Sampler")
        scheduler = gr.Dropdown(["simple", "karras"], value="simple", label="Scheduler")
        seed_val = gr.Number(value=12345, label="Seed")
        rand = gr.Checkbox(value=True, label="Seed zufällig")

    run.click(run_edit, [inp, pr, adv, steps, cfg, sampler, scheduler, seed_val, rand], [out, status, prog])

if __name__ == "__main__":
    threading.Thread(target=ws_listener, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860, css=css)
