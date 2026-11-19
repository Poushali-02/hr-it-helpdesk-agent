"""PII redaction for model output. Tenant contact addresses are allow-listed."""
from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
AADHAAR = re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)")


def redact(text: str, allowed_emails: set[str] | frozenset[str] = frozenset()) -> tuple[str, list[str]]:
    """Return (redacted_text, kinds_found)."""
    found: list[str] = []
    allowed = {e.lower() for e in allowed_emails}

    def email_sub(m: re.Match) -> str:
        if m.group(0).lower() in allowed:
            return m.group(0)
        found.append("email")
        return "[REDACTED_EMAIL]"

    def sub(kind: str, label: str):
        def f(_m: re.Match) -> str:
            found.append(kind)
            return label
        return f

    text = EMAIL.sub(email_sub, text)
    text = PAN.sub(sub("pan", "[REDACTED_PAN]"), text)
    text = PHONE.sub(sub("phone", "[REDACTED_PHONE]"), text)
    text = AADHAAR.sub(sub("aadhaar", "[REDACTED_AADHAAR]"), text)
    return text, found
