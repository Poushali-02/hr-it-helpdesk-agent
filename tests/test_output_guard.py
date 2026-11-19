from helpdesk.config import load_tenant
from helpdesk.guardrails.output_guard import run_output_guard
from helpdesk.retriever import Chunk

T = load_tenant()
CH = [Chunk("leave-policy.md", "Carry-forward", "text", 0.8)]


def test_canary_blocked():
    r = run_output_guard("my token is CANARY-abc", T, "CANARY-abc", False, [])
    assert r.text == T.refusal and "canary_leak_blocked" in r.actions


def test_pii_redacted_in_answer():
    r = run_output_guard("Phone is +91 98100 10102", T, "CANARY-x", False, [])
    assert "[REDACTED_PHONE]" in r.text


def test_ungrounded_replaced():
    r = run_output_guard("Contractors get 26 weeks.", T, "CANARY-x", True, [])
    assert r.text == T.not_found


def test_sources_appended_when_missing():
    r = run_output_guard("Casual leave lapses.", T, "CANARY-x", True, CH)
    assert "Sources: leave-policy.md > Carry-forward" in r.text


def test_existing_sources_kept():
    ans = "Casual leave lapses.\nSources: leave-policy.md > Carry-forward"
    r = run_output_guard(ans, T, "CANARY-x", True, CH)
    assert r.text == ans


def test_not_found_message_gets_no_sources():
    r = run_output_guard(T.not_found, T, "CANARY-x", True, CH)
    assert "Sources:" not in r.text
