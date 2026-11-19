"""Chunk policy markdown by heading, embed locally, upsert into pgvector."""
from __future__ import annotations

import re

import numpy as np

from .config import ROOT
from .db import connect, embedder


def chunk_markdown(doc: str, text: str) -> list[dict]:
    """One chunk per '## ' section; the doc title is prepended for retrieval context."""
    title_m = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_m.group(1).strip() if title_m else doc
    parts = re.split(r"^##\s+", text, flags=re.M)[1:]
    chunks = []
    for part in parts:
        heading, _, body = part.partition("\n")
        body = body.strip()
        if body:
            chunks.append(
                {"doc": doc, "section": heading.strip(), "content": f"{title} - {heading.strip()}\n{body}"}
            )
    return chunks


def main() -> None:
    chunks: list[dict] = []
    for p in sorted((ROOT / "data" / "policies").glob("*.md")):
        chunks += chunk_markdown(p.name, p.read_text(encoding="utf-8"))
    vecs = list(embedder().embed([c["content"] for c in chunks]))
    with connect() as conn:
        conn.execute("TRUNCATE policy_chunks RESTART IDENTITY")
        for c, v in zip(chunks, vecs):
            conn.execute(
                "INSERT INTO policy_chunks (doc, section, content, embedding) VALUES (%s,%s,%s,%s)",
                (c["doc"], c["section"], c["content"], np.asarray(v, dtype=np.float32)),
            )
    print(f"Ingested {len(chunks)} chunks from {len({c['doc'] for c in chunks})} documents.")


if __name__ == "__main__":
    main()
