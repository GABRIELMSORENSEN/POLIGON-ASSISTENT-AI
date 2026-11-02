"""Online inference providers for POLIGON.

API credentials are kept in the operating system credential vault via keyring.
The local model remains the default and no provider is contacted unless selected.
"""
import json
import secrets
import keyring
import httpx
from . import state

SERVICE = "POLIGON online providers"
# Checked against Google Gemini API pricing on 2026-11-02. Keep paid/unknown models out of the no-cost selector.
GEMINI_FREE_MODEL_IDS = {"gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"}
PROVIDERS = {
    "gemini": {
        "name": "Google Gemini API",
        "base": "https://generativelanguage.googleapis.com/v1beta",
        "docs": "https://ai.google.dev/gemini-api/docs",
        "free": "Plano gratuito com limites por modelo/região; confirme a cota no AI Studio."
    },
    "openrouter": {
        "name": "OpenRouter",
        "base": "https://openrouter.ai/api/v1",
        "docs": "https://openrouter.ai/models",
        "free": "Use somente IDs :free ou openrouter/free; limites gratuitos variam."
    },
    "cerebras": {
        "name": "Cerebras Inference",
        "base": "https://api.cerebras.ai/v1",
        "docs": "https://inference-docs.cerebras.ai/",
        "free": "Crédito promocional de avaliação pode exigir cartão e expirar; não é gratuito permanente."
    },
    "deepseek": {
        "name": "DeepSeek API",
        "base": "https://api.deepseek.com",
        "docs": "https://api-docs.deepseek.com/",
        "free": "API paga por uso. Não há gratuidade permanente garantida; confira preço antes de enviar tarefas."
    },
    "xai": {
        "name": "xAI / Grok API",
        "base": "https://api.x.ai/v1",
        "docs": "https://docs.x.ai/",
        "free": "API comercial. Não é incluída em uma assinatura ChatGPT e não há uso gratuito permanente garantido."
    },
    "mistral": {
        "name": "Mistral API",
        "base": "https://api.mistral.ai/v1",
        "docs": "https://docs.mistral.ai/",
        "free": "API paga conforme modelo e uso; confira preços e eventuais créditos de avaliação."
    },
    "openai": {
        "name": "OpenAI API",
        "base": "https://api.openai.com/v1",
        "docs": "https://platform.openai.com/docs",
        "free": "API paga por uso. A assinatura ChatGPT não inclui créditos de API."
    }
}

def _keyring():
    backend = keyring.get_keyring()
    if getattr(backend, "priority", 0) <= 0:
        raise RuntimeError("Nenhum cofre seguro do sistema está disponível. Configure o Gerenciador de Credenciais do Windows ou um cofre seguro do sistema.")
    return keyring

def credential(provider):
    if provider not in PROVIDERS:
        raise ValueError("Provedor desconhecido.")
    return _keyring().get_password(SERVICE, provider)

def save_credential(provider, api_key):
    if provider not in PROVIDERS:
        raise ValueError("Provedor desconhecido.")
    api_key = api_key.strip()
    if not 12 <= len(api_key) <= 512:
        raise ValueError("Chave de API inválida.")
    _keyring().set_password(SERVICE, provider, api_key)

def remove_credential(provider):
    try:
        _keyring().delete_password(SERVICE, provider)
    except keyring.errors.PasswordDeleteError:
        pass

def _request(provider, method, path, api_key, **kwargs):
    cfg = PROVIDERS[provider]
    headers = dict(kwargs.pop("headers", {}))
    if provider == "gemini":
        headers["x-goog-api-key"] = api_key
    else:
        headers["Authorization"] = "Bearer " + api_key
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/GABRIELMSORENSEN/POLIGON-ASSISTENT-AI"
        headers["X-Title"] = "POLIGON"
    with httpx.Client(timeout=35, follow_redirects=False) as client:
        response = client.request(method, cfg["base"] + path, headers=headers, **kwargs)
        if response.status_code >= 400:
            detail = response.text[:700]
            if response.status_code in (401, 403):
                detail = "Chave inválida ou sem permissão. " + detail
            raise RuntimeError(f"{cfg['name']} ({response.status_code}): {detail}")
        return response.json()

def list_models(provider):
    key = credential(provider)
    if not key:
        raise RuntimeError("Conecte uma chave de API primeiro.")
    if provider == "gemini":
        data = _request(provider, "GET", "/models?pageSize=1000", key)
        result = []
        for item in data.get("models", []):
            methods = item.get("supportedGenerationMethods", [])
            name = item.get("name", "")
            if "generateContent" in methods and name and name.removeprefix("models/") in GEMINI_FREE_MODEL_IDS:
                result.append({
                    "id": name.removeprefix("models/"),
                    "name": item.get("displayName", name),
                    "description": item.get("description", "")[:220],
                    "free_note": "Modelo incluído na lista gratuita consultada em 2026-11-02; cotas e disponibilidade podem mudar."
                })
        return sorted(result, key=lambda x: x["id"])
    if provider == "openrouter":
        data = _request(provider, "GET", "/models", key)
        result = [{
            "id": "openrouter/free",
            "name": "Free Models Router (automático)",
            "description": "Escolhe um modelo gratuito disponível em cada chamada.",
            "free_note": "Somente roteamento gratuito."
        }]
        for item in data.get("data", []):
            ident = item.get("id", "")
            pricing = item.get("pricing") or {}
            if ident.endswith(":free") and str(pricing.get("prompt", "0")) == "0" and str(pricing.get("completion", "0")) == "0":
                result.append({
                    "id": ident,
                    "name": item.get("name", ident),
                    "description": (item.get("description") or "")[:220],
                    "free_note": "Variante gratuita; sujeita a limites e disponibilidade."
                })
        return result
    data = _request(provider, "GET", "/models", key)
    result = []
    for item in data.get("data", []):
        ident = item.get("id", "")
        if ident:
            result.append({
                "id": ident,
                "name": item.get("name", ident),
                "description": (item.get("description") or "")[:220],
                "free_note": PROVIDERS[provider]["free"]
            })
    return result

def overview():
    active = state.get("online_provider", "local")
    active_model = state.get("online_model", "")
    result = []
    for ident, cfg in PROVIDERS.items():
        try:
            connected = bool(credential(ident))
        except Exception:
            connected = False
        result.append({
            "id": ident, "name": cfg["name"], "connected": connected,
            "active": active == ident, "active_model": active_model if active == ident else "",
            "docs": cfg["docs"], "free_note": cfg["free"]
        })
    return {"active_provider": active, "active_model": active_model, "providers": result}

def connect(provider, api_key):
    save_credential(provider, api_key)
    try:
        models = list_models(provider)
        if not models:
            raise RuntimeError("A chave foi aceita, mas o provedor não retornou modelos compatíveis.")
        return {"connected": True, "models": models, "provider": provider}
    except Exception:
        remove_credential(provider)
        raise

def select(provider, model):
    if provider not in PROVIDERS:
        raise ValueError("Provedor inválido.")
    if not credential(provider):
        raise RuntimeError("Conecte o provedor antes de selecioná-lo.")
    available = list_models(provider)
    if model not in {m["id"] for m in available}:
        raise ValueError("Modelo não encontrado no catálogo atual do provedor.")
    state.set("online_provider", provider)
    state.set("online_model", model)
    return {"provider": provider, "model": model}

def _openai_messages(messages):
    out = []
    names = {}
    for msg in messages:
        role = msg.get("role")
        if role == "system":
            out.append({"role": "system", "content": msg.get("content") or ""})
        elif role in ("user", "assistant"):
            item = {"role": role, "content": msg.get("content") or ""}
            if msg.get("tool_calls"):
                item["tool_calls"] = msg["tool_calls"]
                for call in msg["tool_calls"]:
                    names[call["id"]] = call["function"]["name"]
            out.append(item)
        elif role == "tool":
            out.append({"role": "tool", "tool_call_id": msg.get("tool_call_id"), "content": msg.get("content", "")})
    return out

def _clean_gemini_schema(value):
    if isinstance(value, list):
        return [_clean_gemini_schema(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_gemini_schema(item) for key, item in value.items() if key not in {"additionalProperties", "default", "$schema"}}
    return value

def _gemini_schema(schema):
    fn = schema["function"]
    params = _clean_gemini_schema(fn.get("parameters") or {"type": "object", "properties": {}})
    return {"name": fn["name"], "description": fn.get("description", ""), "parameters": params}

def _gemini_messages(messages):
    contents, system, pending = [], "", {}
    for msg in messages:
        role = msg.get("role")
        if role == "system":
            system = msg.get("content") or ""
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": msg.get("content") or ""}]})
        elif role == "assistant":
            parts = []
            if msg.get("content"):
                parts.append({"text": msg["content"]})
            for call in msg.get("tool_calls", []):
                fn = call["function"]
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args)
                pending[call["id"]] = fn["name"]
                parts.append({"functionCall": {"name": fn["name"], "args": args}})
            if parts:
                contents.append({"role": "model", "parts": parts})
        elif role == "tool":
            name = pending.pop(msg.get("tool_call_id"), "tool_result")
            try:
                response = json.loads(msg.get("content") or "{}")
            except Exception:
                response = {"result": msg.get("content", "")}
            contents.append({"role": "user", "parts": [{"functionResponse": {"name": name, "response": response}}]})
    return contents, system

def chat(messages, tools=None, max_tokens=1024):
    provider = state.get("online_provider", "local")
    model = state.get("online_model", "")
    if provider not in PROVIDERS or not model:
        raise RuntimeError("Selecione um provedor e um modelo online na aba Modelos.")
    key = credential(provider)
    if not key:
        raise RuntimeError("A chave do provedor não está mais disponível. Reconecte na aba Modelos.")
    if provider in ("openrouter", "cerebras", "deepseek", "xai", "mistral", "openai"):
        body = {
            "model": model,
            "messages": _openai_messages(messages),
            "temperature": 0.2,
            "max_tokens": max_tokens
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        data = _request(provider, "POST", "/chat/completions", key, json=body)
        message = data["choices"][0]["message"]
        return message
    contents, system = _gemini_messages(messages)
    body = {"contents": contents, "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = [{"functionDeclarations": [_gemini_schema(t) for t in tools]}]
        body["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
    data = _request(provider, "POST", "/" + model.removeprefix("models/") + ":generateContent", key, json=body)
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini não retornou candidatos: " + json.dumps(data.get("promptFeedback", {}), ensure_ascii=False))
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if p.get("text"))
    calls = []
    for part in parts:
        fn = part.get("functionCall")
        if fn:
            calls.append({"id": "call_" + secrets.token_hex(8), "type": "function",
                          "function": {"name": fn["name"], "arguments": json.dumps(fn.get("args") or {}, ensure_ascii=False)}})
    result = {"role": "assistant", "content": text}
    if calls:
        result["tool_calls"] = calls
    return result
