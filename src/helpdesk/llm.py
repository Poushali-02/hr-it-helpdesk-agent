"""Provider-agnostic chat model factory. Model IDs come only from .env."""
from __future__ import annotations

import os

from langchain.chat_models import init_chat_model

from .config import PROVIDER_MAP, get_settings


def _build(model: str | None, var: str):
    s = get_settings()
    if not model:
        raise RuntimeError(f"{var} is not set. Copy .env.example to .env and set {var} (and your API key).")
    if s.provider not in PROVIDER_MAP:
        raise RuntimeError(f"LLM_PROVIDER must be one of {sorted(PROVIDER_MAP)}, got {s.provider!r}")
    timeout = float(os.getenv("LLM_TIMEOUT", "60"))  # per request; a stalled call is retried instead of hanging
    return init_chat_model(
        model, model_provider=PROVIDER_MAP[s.provider], temperature=0, max_retries=6, timeout=timeout
    )


def get_llm():
    return _build(get_settings().llm_model, "LLM_MODEL")


def get_guard_llm():
    return _build(get_settings().guard_model, "GUARD_MODEL")


def msg_text(msg) -> str:
    """Plain text of a message regardless of provider content format."""
    try:
        t = msg.text
        if isinstance(t, str):
            return str(t)
    except Exception:
        pass
    c = getattr(msg, "content", "")
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c)
