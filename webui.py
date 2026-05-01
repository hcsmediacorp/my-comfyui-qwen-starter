import os
import json
import random
import time
from pathlib import Path

import requests
import gradio as gr

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
WORKFLOW_PATH = Path("/workspace/ComfyUI/workflow_qwen_lightning_4step.json")
INPUT_DIR = Path("/workspace/ComfyUI/input")
OUTPUT_DIR = Path("/workspace/ComfyUI/output")

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_workflow():
    if WORKFLOW_PATH.exists():
        return json.loads(WORKFLOW_PATH.read_text())
    return {"prompt": {}}

def run_edit(image, prompt):
    if image is None:
        return None, "Bitte ein Bild hochladen."
    if not prompt or not prompt.strip():
        return None, "Bitte einen Prompt eingeben."

    ts = int(time.time())
    in_name = f"shwty_input_{ts}.png"
    image.save(INPUT_DIR / in_name)

    seed = random.randint(1, 2_147_483_647)
    wf = load_workflow()

    # Best-effort node patching
    try:
        for node in wf.get("nodes", []):
            t = node.get("type", "")
            vals = node.get("widgets_values", [])
            if t == "KSampler" and len(vals) >= 4:
                vals[0] = seed      # seed
                vals[2] = 4         # steps fixed
                vals[3] = 1.1       # cfg fixed
            elif t == "CLIPTextEncode" and vals:
                if "blurry" in str(vals[0]).lower():
                    continue
                vals[0] = prompt.strip()
    except Exception:
        pass

    # Queue prompt (if Comfy API ready)
    try:
        r = requests.post(f"{COMFY_URL}/prompt", json={"prompt": wf}, timeout=20)
        if r.status_code >= 300:
            return None, f"ComfyUI Fehler: {r.status_code} {r.text[:200]}"
    except Exception as e:
        return None, f"ComfyUI nicht erreichbar: {e}"

    return image, f"Job gestartet. Seed (auto): {seed} | Steps: 4 | CFG: 1.1"

css = """
body { background:#000 !important; color:#d7ffe8 !important; }
.gradio-container { max-width: 980px !important; margin: 0 auto; }
h1,h2,h3,p,label { color:#d7ffe8 !important; }
button { border:1px solid #00f5ff !important; }
"""

with gr.Blocks(css=css, title="SHWTY Qwen Edit") as demo:
    gr.Markdown("""
# SHWTY Image Edit Studio
Einfache Bedienung für **Mobile & Desktop**.

- Upload Bild
- Prompt eingeben
- Start drücken

**Auto-Settings (fix):** 4 Steps, Random Seed, CFG 1.1
""")

    with gr.Row():
        with gr.Column(scale=1):
            inp = gr.Image(type="pil", label="Bild für Edit")
            pr = gr.Textbox(label="Prompt", placeholder="z. B. verbessere Licht, erhalte Gesicht und Komposition")
            run = gr.Button("Edit starten")
        with gr.Column(scale=1):
            out = gr.Image(label="Vorschau / Letztes Bild")
            status = gr.Textbox(label="Status", interactive=False)

    with gr.Accordion("Advanced (voreingestellt)", open=False):
        gr.Markdown("""
- Steps: **4** (fix)
- Seed: **random** (automatisch)
- CFG: **1.1** (fix)
- Sampler: **dpmpp_2m + karras**
""")

    run.click(fn=run_edit, inputs=[inp, pr], outputs=[out, status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
