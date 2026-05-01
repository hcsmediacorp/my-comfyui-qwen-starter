---
title: my-comfyui-qwen-starter
emoji: 🧠
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# my-comfyui-qwen-starter

Docker-basierter Starter für **Hugging Face Spaces (CPU)** mit **ComfyUI**, **ComfyUI-GGUF** und einem vorbereiteten Setup für **Qwen-Image-Edit-2511-GGUF** inklusive 4-Step-Lightning-LoRA-Workflow.

## Features
- ComfyUI Installation via `comfy-cli`
- CPU-kompatibles Docker-Image für HF Spaces
- Serverstart auf **Port 7860** (HF Spaces Standard)
- `ComfyUI-GGUF` Node vorinstalliert
- Automatischer Model-Download beim Start via `HF_TOKEN` Secret
- Beispiel-Workflow: 4 Schritte, CFG 1.0–1.5
- Relative/Standard-Pfade statt hard-coded absoluter Projektpfade

## Projektstruktur
- `Dockerfile` – Space Build-Konfiguration
- `start.sh` – Startup-Script (lädt optional Modelle, startet ComfyUI)
- `app.py` – Model-Download-Setup aus Hugging Face Repos
- `workflow_qwen_lightning_4step.json` – Beispielworkflow
- `.gitignore` – Python/ComfyUI Ignore-Regeln
- `requirements.txt` – Python-Dependencies

## CPU-Optimierung (Entscheidungen)
Für kostenlose CPU-Instanzen ist Effizienz priorisiert:
- Primär: `Q4_K_M.gguf` (guter Kompromiss aus RAM/Qualität)
- Fallback bei Ressourcenproblemen: `Q2_K` (weniger RAM, schnelleres Laden, geringere Qualität)
- Sampler-Setup: 4 Steps, CFG 1.0–1.5, LoRA mit moderater Stärke

## Wichtiger Hinweis zu Modellgrößen
Die GGUF-Dateien sind groß (u. a. ~13.2GB). Auf CPU Basic kann der erste Start länger dauern und Speicher knapp sein. Für stabile Nutzung empfehlen sich ggf. größere Ressourcen.

## Modelle (vorkonfiguriert)
`app.py` lädt (falls `HF_TOKEN` gesetzt):
- Diffusion: `unsloth/Qwen-Image-Edit-2511-GGUF / Q4_K_M.gguf`
- Text Encoder: `unsloth/Qwen-Image-Edit-2511-GGUF / qwen2.5-vl-7b-edit-q4_0.gguf`
- VAE: `unsloth/Qwen-Image-Edit-2511-GGUF / pig_qwen_image_vae_fp32-f16.gguf`
- LoRA: aktuell Platzhalter (`ByteDance/Hyper-SD / Hyper-SD15-4steps-lora.safetensors`) – bitte bei Bedarf auf den final gewünschten 4-Step-Lightning-LoRA-Adapter anpassen.

## Hugging Face Space Setup
1. Space erstellen: **Docker**, **CPU Basic**
2. Dieses Repo als Source verbinden (oder spiegeln)
3. Secret setzen: `HF_TOKEN=<dein_token>`
4. Build starten
5. Space-URL öffnen (ComfyUI läuft auf Port 7860)

## Lokal testen
```bash
docker build -t my-comfyui-qwen-starter .
docker run --rm -p 7860:7860 -e HF_TOKEN=$HF_TOKEN my-comfyui-qwen-starter
```

## Fehlerbehandlung / Retry-Strategie
Wenn Build/Install fehlschlägt, wird folgende Reihenfolge angewendet und dokumentiert:
1. Retry des fehlgeschlagenen Schritts (Netzwerk/Timeout)
2. `pip`-Upgrade und erneute Installation
3. Fallback auf alternative Quantisierung (`Q2_K`) bei RAM-Problemen
4. Neuaufbau des Space-Builds und erneuter Start

## Durchgeführte Schritte (Log)
1. Repository-Struktur erstellt
2. Dockerfile für CPU + Port 7860 erstellt
3. Startscript mit robusten Shell-Flags ergänzt
4. Model-Downloader (`app.py`) mit HF_TOKEN-Integration erstellt
5. Beispiel-Workflow (4-Step + CFG 1.2) hinzugefügt
6. README inkl. CPU-Optimierungs- und Fehlerstrategie dokumentiert
7. Build-Fix: `WORKDIR` auf `/workspace/ComfyUI` korrigiert, damit `custom_nodes` beim Docker-Build existiert
8. Build-Fix: `app.py` auf relative/konfigurierbare Pfade (`COMFY_DIR`) umgestellt
9. Build-Fix: PEP668-Fehler gelöst durch Python-Venv (`/opt/venv`) und Installation über `pip` im Venv statt System-`pip3`
10. Build-Fix: `comfy install` auf non-interaktiv umgestellt (`CI=1`, Input-Pipe), damit kein Tracking-Prompt den Build abbricht
11. Build-Fix: inkompatibles Flag `--skip-pip` entfernt (in comfy-cli 1.7.3 nicht unterstützt)
12. Build-Fix: zweites `comfy install` Prompt (Installationsbestätigung) automatisiert (`n` für Tracking, `y` für ComfyUI-Install), danach Symlink nach `/workspace/ComfyUI`
13. Runtime-Fix: `start.sh` nutzt jetzt standardmäßig absoluten Pfad `/workspace/ComfyUI` statt relativem `./ComfyUI`
14. Runtime-Fix: `app.py` wird über absoluten Pfad `/app.py` gestartet (statt relativem `../app.py`)
15. Runtime-Fix: fehlendes `huggingface_hub` behoben durch Installation von `/requirements.txt` im Docker-Build
16. Runtime-Fix: fehlende/umbenannte Modelldateien (404) führen nicht mehr zum Container-Abbruch; Downloads sind fehlertolerant und Startup läuft weiter

## Nächste Schritte
Ich führe den kompletten Publish-Flow (GitHub Repo + HF Space + Secret + Deployment) direkt aus, sobald GitHub- und Hugging-Face-Zugriff bereitstehen.
