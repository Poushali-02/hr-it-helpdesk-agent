"""Integration tests for the MCP tools. Need `make up seed` (skipped if the DB is unreachable)."""
import os

import psycopg
import pytest

from helpdesk.config import get_settings

S = get_settings()
os.environ.setdefault("MCP_DATABASE_URL", S.mcp_database_url)


def _db_up() -> bool:
    try:
        psycopg.connect(S.mcp_database_url, connect_timeout=3).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_up(), reason="database not running")

from mcp_server import server  # noqa: E402


def as_user(uid: str):
    os.environ["HELPDESK_REQUESTER"] = uid
    os.environ["HR_ADMIN_ID"] = "E001"


def test_own_balance():
    as_user("E102")
    r = server.get_leave_balance("E102", "casual")
    assert r["balances"] == [{"leave_type": "casual", "entitled": 12, "used": 4, "remaining": 8}]


def test_all_types():
    as_user("E102")
    r = server.get_leave_balance("E102")
    assert {b["leave_type"]: b["remaining"] for b in r["balances"]} == {"casual": 8, "earned": 9, "sick": 8}


def test_hr_can_read_anyone():
    as_user("E001")
    assert "balances" in server.get_leave_balance("E102")


def test_employee_cannot_read_others():
    as_user("E103")
    assert "Not authorized" in server.get_employee_profile("E102")["error"]


def test_invalid_ids_rejected():
    as_user("E001")
    for bad in ["E102'; DROP TABLE employees;--", "102", "e102", "E1022"]:
        assert "Invalid employee id" in server.get_leave_balance(bad)["error"]


def test_unknown_employee():
    as_user("E001")
    assert "not found" in server.get_employee_profile("E999")["error"]


def test_bad_leave_type():
    as_user("E102")
    assert "Unknown leave_type" in server.get_leave_balance("E102", "x' OR 1=1")["error"]


def test_db_role_is_read_only():
    with psycopg.connect(S.mcp_database_url, autocommit=True) as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("UPDATE leave_balances SET used = 0")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("SELECT * FROM policy_chunks")
