from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

from .config import ROOT, get_settings
from fastembed import TextEmbedding

_embedder: TextEmbedding | None = None


def connect(url: str | None = None, vector: bool = True) -> psycopg.Connection:
    conn = psycopg.connect(url or get_settings().database_url, autocommit=True)
    if vector:
        register_vector(conn)
    return conn


def embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(
            model_name=get_settings().embed_model,
            cache_dir=str(ROOT / ".cache" / "fastembed"),
        )
    return _embedder
