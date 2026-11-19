"""Loads .env and config/tenant.yaml. Everything client-specific comes from tenant.yaml."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

PROVIDER_MAP = {"gemini": "google_genai", "anthropic": "anthropic", "openai": "openai"}


@dataclass
class Tenant:
    company_name: str
    assistant_name: str
    tone: str
    contacts: dict[str, str]
    in_scope: list[str]
    refusal_message: str
    not_found_message: str
    hr_admin_id: str = "E001"

    @property
    def refusal(self) -> str:
        return self.refusal_message.format(company_name=self.company_name)

    @property
    def not_found(self) -> str:
        return self.not_found_message.format(
            hr_contact=self.contacts["hr"], it_contact=self.contacts["it"]
        )

    @property
    def allowed_emails(self) -> set[str]:
        return {v.lower() for v in self.contacts.values()}


@lru_cache(maxsize=1)
def load_tenant(path: str | None = None) -> Tenant:
    p = Path(path or os.getenv("TENANT_FILE") or ROOT / "config" / "tenant.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Tenant(**data)


def _env_model(name: str) -> str | None:
    v = (os.getenv(name) or "").strip()
    if not v or v.startswith("<"):
        return None
    return v


@dataclass
class Settings:
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini").lower())
    llm_model: str | None = field(default_factory=lambda: _env_model("LLM_MODEL"))
    guard_model: str | None = field(default_factory=lambda: _env_model("GUARD_MODEL"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    mcp_database_url: str = field(default_factory=lambda: os.getenv("MCP_DATABASE_URL", ""))
    embed_model: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5"))
    threshold: float = field(default_factory=lambda: float(os.getenv("SIMILARITY_THRESHOLD", "0.45")))
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "4")))
    price_in: float | None = field(default_factory=lambda: _float(os.getenv("PRICE_IN_PER_M")))
    price_out: float | None = field(default_factory=lambda: _float(os.getenv("PRICE_OUT_PER_M")))


def _float(v: str | None) -> float | None:
    try:
        return float(v) if v else None
    except ValueError:
        return None


def get_settings() -> Settings:
    return Settings()
