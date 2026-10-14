"""
ai_provider.py — طبقة تجريد مزودي الذكاء الاصطناعي (PRD §15).

- كل المزودين عبر واجهة OpenAI-compatible نفسها (chat/completions):
  OpenAI / OpenRouter / Z.AI / Ollama / LM Studio / Google (نقطة openai/).
- الترتيب من env: AI_PROVIDER_ORDER (افتراضي: openrouter,openai,google).
- مفاتيح المزودين من env فقط (لا أسرار في الكود أبدا):
  OPENROUTER_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY (+ نماذج اختيارية).
- ضوابط التكلفة: AI_MAX_TOKENS (افتراضي 1024 — يكفي النماذج الاستدلالية
  التي تستهلك جزءا في التفكير) + AI_TIMEOUT_S (افتراضي 25).
- السلوك: يجرب بالترتيب مع سقوط للمزود التالي عند أي فشل، ويعيد
  {"text", "provider"} أو None عندما لا يوجد مزود مهيأ — فيعيد المتصل
  لمساره المحلي (القالب/heuristic) دون أي خطأ.
"""
from __future__ import annotations

import os

DEFAULT_ORDER = ("openrouter", "openai", "google")

PROVIDERS = {
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "model_default": "openrouter/auto",
    },
    "openai": {
        "base": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "model_default": "gpt-4o-mini",
    },
    "google": {
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GOOGLE_API_KEY",
        "model_env": "GOOGLE_MODEL",
        "model_default": "gemini-2.5-flash",
    },
    "zai": {
        "base": "https://api.z.ai/api/paas/v4",
        "key_env": "ZAI_API_KEY",
        "model_env": "ZAI_MODEL",
        "model_default": "glm-4-flash",
    },
    "ollama": {
        "base": "http://127.0.0.1:11434/v1",
        "key_env": "OLLAMA_API_KEY",
        "model_env": "OLLAMA_MODEL",
        "model_default": "qwen2.5:7b",
    },
    "lmstudio": {
        "base": "http://127.0.0.1:1234/v1",
        "key_env": "LMSTUDIO_API_KEY",
        "model_env": "LMSTUDIO_MODEL",
        "model_default": "local-model",
    },
}

# المزودات المحلية بلا مفتاح حقيقي (تعمل بمفتاح وهمي).
_NO_KEY = ("ollama", "lmstudio")


def _cfg(name: str) -> dict | None:
    spec = PROVIDERS.get(name)
    if not spec:
        return None
    key = os.getenv(spec["key_env"], "")
    if not key and name not in _NO_KEY:
        return None
    return {
        "name": name,
        "base": os.getenv("PROVIDER_BASE_" + name.upper(), spec["base"]),
        "key": key or "ollama",
        "model": os.getenv(spec["model_env"], spec["model_default"]),
    }


def provider_order() -> list:
    raw = os.getenv("AI_PROVIDER_ORDER", ",".join(DEFAULT_ORDER))
    return [p.strip().lower() for p in raw.split(",") if p.strip().lower() in PROVIDERS]


def provider_health() -> dict:
    """حالة الصحة: مهيأ (مفتاح موجود) أم لا — بلا أي اتصال شبكي."""
    out = {}
    for name, spec in PROVIDERS.items():
        if name in _NO_KEY:
            # المحليتان: مهيأتان فقط عند ضبط النموذج صراحة
            # (تجنب مهلة localhost على serverless).
            out[name] = bool(os.getenv(spec["model_env"], ""))
        else:
            out[name] = bool(os.getenv(spec["key_env"], ""))
    return out


def generate(prompt: str, system: str = "", max_tokens: int | None = None) -> dict | None:
    """أول استخدام حقيقي واحد: يعيد {"text", "provider"} أو None."""
    import httpx

    max_tok = max_tokens or int(os.getenv("AI_MAX_TOKENS", "1024"))
    timeout = float(os.getenv("AI_TIMEOUT_S", "25"))
    for name in provider_order():
        cfg = _cfg(name)
        if not cfg:
            continue
        try:
            r = httpx.post(
                cfg["base"].rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + cfg["key"]},
                json={
                    "model": cfg["model"],
                    "messages": [
                        *([{"role": "system", "content": system}] if system else []),
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tok,
                    "temperature": 0.4,
                },
                timeout=timeout,
            )
            if r.status_code != 200:
                continue
            text = (r.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
            if text:
                return {"text": text, "provider": name}
        except Exception:
            continue
    return None
