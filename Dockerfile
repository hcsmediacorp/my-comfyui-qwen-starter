FROM node:22-slim

ENV CUDA_VISIBLE_DEVICES=-1
ENV TORCH_CUDA_ARCH_LIST=""
ENV PYTHONUNBUFFERED=1
ENV COMFYUI_HIGH_VRAM_THRESHOLD=1
ENV OMP_NUM_THREADS=1

RUN apt-get update && apt-get install -y \
  git python3 python3-pip python3-venv curl wget \
  libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# ComfyUI Installation mit comfy-cli (PEP668-safe via venv)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install comfy-cli
# Non-interaktiv für CI/Space-Build
ENV CI=1
RUN printf 'n\ny\n' | comfy install --cpu
# Zusätzliche Runtime-Dependencies laut ComfyUI-Startup-Logs
RUN /opt/venv/bin/python3 -m pip install -r /root/comfy/ComfyUI/requirements.txt
RUN /opt/venv/bin/python3 -m pip install alembic Pillow blake3
RUN mkdir -p /workspace && ln -s /root/comfy/ComfyUI /workspace/ComfyUI

WORKDIR /workspace/ComfyUI

# ComfyUI-GGUF node für GGUF-Unterstützung installieren
RUN cd custom_nodes && git clone https://github.com/city96/ComfyUI-GGUF.git && \
  cd ComfyUI-GGUF && pip3 install -r requirements.txt

COPY --chown=root:root requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY --chown=root:root start.sh /start.sh
COPY --chown=root:root app.py /app.py
COPY --chown=root:root webui.py /webui.py
RUN chmod +x /start.sh

EXPOSE 7860
CMD ["/start.sh"]
