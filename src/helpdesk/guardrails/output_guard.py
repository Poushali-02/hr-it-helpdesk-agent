"""Output guard: canary check, PII redaction, groundedness, citations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .pii import redact


@dataclass
class OutputResult:
    text: str
    actions: list[str] = field(default_factory=list)


def sources_line(chunks) -> str:
    seen, items = set(), []
    for c in chunks:
        key = (c.doc, c.section)
        if key not in seen:
            seen.add(key)
            items.append(f"{c.doc} > {c.section}")
    return "Sources: " + "; ".join(items)


def run_output_guard(answer: str, tenant, canary: str, searched: bool, chunks) -> OutputResult:
    actions: list[str] = []

    if canary and canary in answer:
        return OutputResult(tenant.refusal, ["canary_leak_blocked"])

    text, kinds = redact(answer, tenant.allowed_emails)
    if kinds:
        actions.append("pii_redacted:" + ",".join(sorted(set(kinds))))

    # Groundedness: the model searched the policies but nothing relevant came back.
    if searched and not chunks:
        return OutputResult(tenant.not_found, actions + ["ungrounded_replaced"])

    # Citations: a policy answer must carry its sources.
    is_not_found = "couldn't find" in text.lower()
    if chunks and not is_not_found and not re.search(r"^\s*Sources?:", text, re.I | re.M):
        text = text.rstrip() + "\n\n" + sources_line(chunks)
        actions.append("sources_appended")

    return OutputResult(text, actions)
