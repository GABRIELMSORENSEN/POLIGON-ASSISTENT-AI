"""Creator tools for POLIGON Studio.

Provider credentials are stored in the OS credential vault. Generation is opt-in:
these APIs contact paid external services only after an explicit user action.
"""
import re
import secrets
import time
from pathlib import Path
import httpx
import keyring
from fastapi import HTTPException
from . import state

SERVICE = "POLIGON Studio providers"
RUNWAY_BASE = "https://api.dev.runwayml.com"
ELEVEN_BASE = "https://api.elevenlabs.io"
OUTPUT_DIR = state.ROOT / "studio" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RUNWAY_VERSION = "2024-11-06"

def _vault():
    backend = keyring.get_keyring()
    if getattr(backend, "priority", 0) <= 0:
        raise RuntimeError("Nenhum cofre seguro do sistema está disponível.")
    return keyring

def credential(provider):
    if provider not in {"runway", "elevenlabs"}:
        raise ValueError("Provedor Studio desconhecido.")
    return _vault().get_password(SERVICE, provider)

def connect(provider, api_key):
    if provider not in {"runway", "elevenlabs"}:
        raise ValueError("Provedor Studio desconhecido.")
    value = api_key.strip()
    if not 12 <= len(value) <= 512:
        raise ValueError("Chave de API inválida.")
    _vault().set_password(SERVICE, provider, value)
    return {"provider": provider, "connected": True}

def disconnect(provider):
    try:
        _vault().delete_password(SERVICE, provider)
    except keyring.errors.PasswordDeleteError:
        pass
    return {"provider": provider, "connected": False}

def overview():
    result = []
    for provider, name, docs, note in (
        ("runway", "Runway Dev", "https://docs.dev.runwayml.com/api/", "Geração de imagem/vídeo por API; uso sujeito a créditos e cobrança da conta Dev."),
        ("elevenlabs", "ElevenLabs", "https://elevenlabs.io/docs/api-reference", "Voz, narração e dublagem; uso sujeito aos créditos e limites da conta.")
    ):
        try:
            connected = bool(credential(provider))
        except Exception:
            connected = False
        result.append({"id": provider, "name": name, "connected": connected, "docs": docs, "note": note})
    return {"providers": result}

def voices():
    key = credential("elevenlabs")
    if not key:
        raise RuntimeError("Conecte a chave do ElevenLabs primeiro.")
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.get(ELEVEN_BASE + "/v1/voices", headers={"xi-api-key": key})
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs ({response.status_code}): {response.text[:500]}")
        data = response.json()
    return [{"voice_id": v.get("voice_id"), "name": v.get("name"), "category": v.get("category")} for v in data.get("voices", []) if v.get("voice_id")]

def generate_speech(text, voice_id, model_id="eleven_v4"):
    key = credential("elevenlabs")
    if not key:
        raise RuntimeError("Conecte a chave do ElevenLabs primeiro.")
    text = text.strip()
    voice_id = voice_id.strip()
    if not text or len(text) > 10000:
        raise ValueError("O texto deve ter entre 1 e 10.000 caracteres.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{5,80}", voice_id):
        raise ValueError("ID de voz inválido.")
    if model_id not in {"eleven_v4", "eleven_v4_turbo", "eleven_multilingual_v2", "eleven_flash_v2_5"}:
        raise ValueError("Modelo de voz não permitido.")
    with httpx.Client(timeout=120, follow_redirects=False) as client:
        response = client.post(
            f"{ELEVEN_BASE}/v1/text-to-speech/{voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            json={"text": text, "model_id": model_id}
        )
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs ({response.status_code}): {response.text[:500]}")
        audio = response.content
    if not audio or len(audio) > 40 * 1024 * 1024:
        raise RuntimeError("O áudio retornado está vazio ou excede o limite de 40 MB.")
    name = secrets.token_hex(12) + ".mp3"
    destination = OUTPUT_DIR / name
    destination.write_bytes(audio)
    return {"file": name, "url": f"/api/studio/audio/{name}", "bytes": len(audio), "characters": len(text), "model": model_id}

def start_video(prompt, model="gen4.5", ratio="1280:720", duration=5):
    key = credential("runway")
    if not key:
        raise RuntimeError("Conecte a chave do Runway Dev primeiro.")
    prompt = prompt.strip()
    if not prompt or len(prompt) > 1000:
        raise ValueError("O prompt deve ter entre 1 e 1.000 caracteres.")
    if model not in {"gen4.5", "veo3.1_fast", "veo3.1", "gen4_turbo"}:
        raise ValueError("Modelo de vídeo não permitido.")
    if ratio not in {"1280:720", "720:1280", "1104:832", "832:1104", "960:960"}:
        raise ValueError("Proporção não permitida.")
    if duration not in {5, 10}:
        raise ValueError("Duração deve ser 5 ou 10 segundos.")
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        response = client.post(
            RUNWAY_BASE + "/v1/text_to_video",
            headers={"Authorization": "Bearer " + key, "X-Runway-Version": RUNWAY_VERSION, "Content-Type": "application/json"},
            json={"model": model, "promptText": prompt, "ratio": ratio, "duration": duration}
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Runway ({response.status_code}): {response.text[:600]}")
        data = response.json()
    task_id = data.get("id")
    if not task_id:
        raise RuntimeError("Runway não retornou um ID de tarefa.")
    return {"task_id": task_id, "status": data.get("status", "PENDING"), "provider": "runway"}

def video_task(task_id):
    key = credential("runway")
    if not key:
        raise RuntimeError("Conecte a chave do Runway Dev primeiro.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", task_id):
        raise ValueError("ID de tarefa inválido.")
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.get(
            RUNWAY_BASE + "/v1/tasks/" + task_id,
            headers={"Authorization": "Bearer " + key, "X-Runway-Version": RUNWAY_VERSION}
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Runway ({response.status_code}): {response.text[:500]}")
        data = response.json()
    output = data.get("output") or []
    return {"task_id": task_id, "status": data.get("status", "UNKNOWN"), "output": output, "failure": data.get("failure"), "failure_code": data.get("failureCode")}
