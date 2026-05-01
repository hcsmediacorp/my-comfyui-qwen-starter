FROM node:22-slim

RUN apt-get update && apt-get install -y \
  git python3 python3-pip python3-venv curl wget \
  libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# ComfyUI Installation mit comfy-cli
RUN pip3 install --upgrade pip && pip3 install comfy-cli
RUN comfy install --skip-pip --cpu

WORKDIR /workspace/ComfyUI

# ComfyUI-GGUF node für GGUF-Unterstützung installieren
RUN cd custom_nodes && git clone https://github.com/city96/ComfyUI-GGUF.git && \
  cd ComfyUI-GGUF && pip3 install -r requirements.txt

COPY --chown=root:root start.sh /start.sh
COPY --chown=root:root app.py /app.py
RUN chmod +x /start.sh

EXPOSE 7860
CMD ["/start.sh"]
