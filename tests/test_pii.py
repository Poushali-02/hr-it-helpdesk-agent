from helpdesk.guardrails.pii import redact

ALLOWED = {"hr@northwind.example", "it-helpdesk@northwind.example"}


def test_redacts_personal_email_and_phone():
    out, kinds = redact("Phone +91 98100 10102, mail priya.nair22@gmail.com", ALLOWED)
    assert "[REDACTED_PHONE]" in out and "[REDACTED_EMAIL]" in out
    assert "98100" not in out and "gmail" not in out
    assert set(kinds) == {"phone", "email"}


def test_plain_ten_digit_phone():
    out, _ = redact("call 9810010102 now", ALLOWED)
    assert "[REDACTED_PHONE]" in out


def test_pan_and_aadhaar():
    out, kinds = redact("PAN BQRPN4102C and Aadhaar 1234 5678 9012", ALLOWED)
    assert "[REDACTED_PAN]" in out and "[REDACTED_AADHAAR]" in out
    assert set(kinds) == {"pan", "aadhaar"}


def test_allowlisted_contacts_survive():
    text = "Contact hr@northwind.example or IT-Helpdesk@northwind.example"
    out, kinds = redact(text, ALLOWED)
    assert out == text and kinds == []


def test_leave_numbers_not_touched():
    text = "Casual: entitled 12, used 4, remaining 8. Earned: 15 entitled, 6 used. 2026 policy."
    out, kinds = redact(text, ALLOWED)
    assert out == text and kinds == []
