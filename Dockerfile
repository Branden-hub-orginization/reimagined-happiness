FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y wget unzip curl ffmpeg

# Install LocalAI
RUN wget https://github.com/go-skynet/LocalAI/releases/download/v2.15.0/local-ai-linux-amd64.zip && \
    unzip local-ai-linux-amd64.zip -d /usr/local/bin && chmod +x /usr/local/bin/local-ai

# Download models
RUN mkdir -p /app/models/localai && \
    curl -L -o /app/models/localai/llama3-8b-q4_0.bin https://huggingface.co/TheBloke/LLaMA-3-8B-GGML/resolve/main/ggml-model-q4_0.bin && \
    curl -L -o /app/models/localai/mistral-7b-q4_0.bin https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGML/resolve/main/ggml-model-q4_0.bin && \
    curl -L -o /app/models/localai/gpt-neox-20b-q4_0.bin https://huggingface.co/TheBloke/GPT-NeoX-20B-GGML/resolve/main/ggml-model-q4_0.bin

COPY . .
CMD ["python","agi_mesh.py"]
