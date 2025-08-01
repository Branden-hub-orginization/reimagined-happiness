import requests, json, numpy as np, weaviate, os, torch, socket, asyncio, aiohttp
from fastapi import FastAPI, UploadFile
from transformers import AutoTokenizer, AutoModel, Wav2Vec2Processor, Wav2Vec2Model
from sentence_transformers import SentenceTransformer
from PIL import Image
import torchaudio
from weaver_bus import WeaverBus
from cognitive_core import CognitiveCore

app = FastAPI()
weaver = WeaverBus()
core = CognitiveCore()
weaviate_client = weaviate.Client("http://weaviate:8080")

MODELS = ["llama3-8b-q4_0.bin","mistral-7b-q4_0.bin","gpt-neox-20b-q4_0.bin"]

# Embedding models
text_tok = AutoTokenizer.from_pretrained("intfloat/e5-large-v2")
text_emb = AutoModel.from_pretrained("intfloat/e5-large-v2")
clip_model = SentenceTransformer("clip-ViT-B-32")
wav_proc = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
wav_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h")

def embed_text(t):
    tokens = text_tok(t, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        return text_emb(**tokens).last_hidden_state.mean(dim=1).squeeze().numpy()

def embed_image(img):
    return clip_model.encode(img)

def embed_audio(fp):
    wav,sr = torchaudio.load(fp)
    vals = wav_proc(wav.squeeze().numpy(), sampling_rate=sr, return_tensors="pt").input_values
    with torch.no_grad():
        return wav_model(vals).last_hidden_state.mean(dim=1).squeeze().numpy()

def add_to_mem(vec, meta):
    weaviate_client.data_object.create({"vector": vec.tolist(), **meta}, "Memory")

def query_model(m,prompt):
    payload = {"model": m, "prompt": prompt, "temperature": 0.7, "max_tokens": 512}
    try:
        r = requests.post("http://localhost:8080/v1/completions", json=payload, timeout=60)
        return r.json().get("choices",[{}])[0].get("text","")
    except:
        return "[error]"

async def discover_peers():
    ip = socket.gethostbyname(socket.gethostname())
    subnet = ".".join(ip.split(".")[:-1])
    peers = []
    async with aiohttp.ClientSession() as session:
        for i in range(2,255):
            url = f"http://{subnet}.{i}:8000/ping"
            try:
                async with session.get(url, timeout=0.2) as r:
                    if r.status == 200: peers.append(url)
            except: continue
    return peers

@app.get("/ping")
async def ping():
    return {"status":"alive"}

@app.post("/ask")
async def ask(q: str):
    qv = embed_text(q)
    add_to_mem(qv, {"type":"text","content":q})
    responses = [query_model(m,q) for m in MODELS]
    responses = core.process(q,responses)
    for r in responses:
        rv = embed_text(r)
        add_to_mem(rv, {"type":"text","content":r})
    consensus = " ".join(responses)
    return {"responses": responses, "consensus": consensus}

@app.post("/analyze_image")
async def analyze_image(file: UploadFile):
    img = Image.open(file.file)
    vec = embed_image(img)
    add_to_mem(vec, {"type":"image","content":"[image uploaded]"})
    return {"status":"stored"}

@app.post("/transcribe_audio")
async def transcribe_audio(file: UploadFile):
    path="/tmp/audio.wav"
    with open(path,"wb") as f: f.write(await file.read())
    vec = embed_audio(path)
    add_to_mem(vec, {"type":"audio","content":"[audio uploaded]"})
    return {"status":"stored"}
