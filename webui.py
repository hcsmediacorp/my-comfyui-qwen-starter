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
LAST_ERROR = ""


def ws_listener():
    while True:
        try:
            ws = websocket.create_connection(WS_URL, timeout=30)
            while True:
                data = json.loads(ws.recv())
                t = data.get("type")
                d = data.get("data", {})
                if t == "progress":
                    v = int(d.get("value", 0))
                    m = max(int(d.get("max", 1) or 1), 1)
                    PROGRESS["value"] = int((v / m) * 100)
                    PROGRESS["text"] = f"Generierung läuft: Schritt {v}/{m}"
                elif t == "executing":
                    node = d.get("node")
                    if node is not None:
                        PROGRESS["text"] = f"Bearbeite Node: {node}"
                elif t == "execution_success":
                    PROGRESS["value"] = 100
                    PROGRESS["text"] = "Fertig"
        except Exception:
            PROGRESS["text"] = "Verbindung wird neu aufgebaut …"
            time.sleep(2)


def resolve_checkpoint_name():
    preferred = os.getenv("QWEN_DIFFUSION_FILE", "qwen-image-edit-2511-Q2_K.gguf")
    ckpt_dir = Path("/workspace/ComfyUI/models/checkpoints")
    gguf_dirs = [Path("/workspace/ComfyUI/models/diffusion_models"), Path("/workspace/ComfyUI/models/unet")]

    for d in gguf_dirs:
        p = d / preferred
        if d.exists() and p.exists():
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            target = ckpt_dir / preferred
            if not target.exists():
                try:
                    target.symlink_to(p)
                except Exception:
                    pass

    if ckpt_dir.exists():
        files = sorted([x.name for x in ckpt_dir.iterdir() if x.is_file() or x.is_symlink()])
        if preferred in files:
            return preferred, files
        if files:
            return files[0], files
    return preferred, []


def build_prompt_payload(prompt_text: str, seed: int, steps: int, cfg: float, sampler: str, scheduler: str):
    ckpt, _ = resolve_checkpoint_name()
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "blur, artifacts, distortion", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 768, "batch_size": 1}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(seed),
                "steps": int(steps),
                "cfg": float(cfg),
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "shwty_qwen", "images": ["6", 0]}},
    }


def parse_error(status_code: int, text: str):
    global LAST_ERROR
    try:
        d = json.loads(text)
        err = d.get("error", {})
        typ = err.get("type", "Fehler")
        msg = err.get("message", "Unbekannter Fehler")
        node = err.get("node_id", "-")
        LAST_ERROR = f"{typ} | Node: {node} | {msg}"
        return f"Fehler: {typ} (Node {node}) – {msg}"
    except Exception:
        LAST_ERROR = f"HTTP {status_code}: {text[:200]}"
        return f"Fehler: HTTP {status_code} – Details siehe Log"


def run_edit(image, prompt, adv_enabled, steps, cfg, sampler, scheduler, seed_val, randomize_seed):
    if image is None:
        return None, "Bitte lade ein Bild hoch.", 0
    if not (prompt or "").strip():
        return None, "Bitte gib einen Prompt ein.", 0

    if adv_enabled:
        run_steps, run_cfg = int(steps), float(cfg)
        run_sampler, run_scheduler = sampler, scheduler
        seed = random.randint(1, 2_147_483_647) if randomize_seed else int(seed_val)
    else:
        run_steps, run_cfg = 4, 1.1
        run_sampler, run_scheduler = "euler", "simple"
        seed = random.randint(1, 2_147_483_647)

    image.save(INPUT_DIR / f"input_{int(time.time())}.png")

    ckpt, available = resolve_checkpoint_name()
    if not available:
        return None, "Kein Modell gefunden. Bitte warte, bis der Download abgeschlossen ist, oder lege ein Modell in ComfyUI/models/checkpoints ab.", 0

    payload = {"prompt": build_prompt_payload(prompt.strip(), seed, run_steps, run_cfg, run_sampler, run_scheduler)}

    try:
        PROGRESS["value"] = 1
        PROGRESS["text"] = "Auftrag wird an ComfyUI gesendet …"
        r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
        if r.status_code >= 300:
            return None, parse_error(r.status_code, r.text), 0
    except Exception as e:
        return None, f"ComfyUI nicht erreichbar: {e}", 0

    return image, f"Auftrag gestartet. Seed: {seed} | Steps: {run_steps} | CFG: {run_cfg}", PROGRESS["value"]


def poll_progress():
    return PROGRESS["text"], PROGRESS["value"]


css = """
:root { --bg:#f7f9fc; --card:#ffffff; --text:#1f2937; --accent:#2563eb; --muted:#6b7280; }
body { background:var(--bg) !important; color:var(--text) !important; }
.gradio-container { max-width: 1060px !important; margin: 0 auto; }
.block, .gr-panel, .gr-box, .gr-form, .gr-group { border-radius: 14px !important; }
button { border-radius: 10px !important; }
.primary { background:var(--accent) !important; }
"""

with gr.Blocks(title="SHWTY Image Edit Studio") as demo:
    gr.Markdown("""
# SHWTY Image Edit Studio (v1 Beta)
Einfache Bildbearbeitung mit Qwen/ComfyUI auf CPU.

1. Bild hochladen
2. Wunsch in Textform eingeben
3. **Generieren** klicken
""")
    live = gr.Markdown("**Status:** Bereit")

    with gr.Row():
        with gr.Column(scale=1):
            inp = gr.Image(type="pil", label="1) Bild hochladen")
            pr = gr.Textbox(label="2) Prompt", lines=3, placeholder="z. B. Person am Strand bei Sonnenuntergang")
            adv = gr.Checkbox(label="Erweiterte Einstellungen aktivieren", value=False)
            run = gr.Button("3) Generieren", variant="primary")
        with gr.Column(scale=1):
            out = gr.Image(label="Ausgabe / Vorschau")
            status = gr.Textbox(label="Status & Hinweise", interactive=False)
            prog = gr.Slider(0, 100, value=0, step=1, label="Fortschritt", interactive=False)

    with gr.Accordion("Erweiterte Einstellungen", open=False):
        gr.Markdown("Nur ändern, wenn du bewusst feintunen willst. Standardwerte sind stabil für CPU.")
        steps = gr.Slider(1, 50, value=4, step=1, label="Steps")
        cfg = gr.Slider(0.0, 10.0, value=1.1, step=0.1, label="CFG")
        sampler = gr.Dropdown(["euler", "dpmpp_2m"], value="euler", label="Sampler")
        scheduler = gr.Dropdown(["simple", "karras"], value="simple", label="Scheduler")
        seed_val = gr.Number(value=12345, label="Seed")
        rand = gr.Checkbox(value=True, label="Seed zufällig setzen")

    run.click(run_edit, [inp, pr, adv, steps, cfg, sampler, scheduler, seed_val, rand], [out, status, prog])

    gr.Markdown("""
---
### Credits / Modell-Hinweise
- Unsloth (Qwen2.5-VL GGUF): https://huggingface.co/unsloth/Qwen2.5-VL-7B-Instruct-GGUF
- Qwen Team: https://huggingface.co/Qwen
- LightX Lightning LoRA: https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning

Dieses Projekt nutzt Open-Source-Gewichte; alle Rechte liegen bei den jeweiligen Erstellern.
""")

if __name__ == "__main__":
    threading.Thread(target=ws_listener, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860, css=css)
