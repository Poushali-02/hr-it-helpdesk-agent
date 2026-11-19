"""Read-only HR data MCP server (FastMCP, stdio).

Narrow tools only: no SQL passthrough. Connects with the read-only `helpdesk_ro` role.
Identity comes from the environment (set by the host that launches the server):
  HELPDESK_REQUESTER  the authenticated employee id, e.g. E102
  HR_ADMIN_ID         the HR admin id who may look up anyone (default E001)
  MCP_DATABASE_URL    read-only connection string
"""
from __future__ import annotations

import os
import re

import psycopg
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("northwind-hr-data")

ID_RE = re.compile(r"^E\d{3}$")
LEAVE_TYPES = {"casual", "sick", "earned"}


def _check(employee_id: str) -> str | None:
    """Return an error string if the id is invalid or the requester may not see it."""
    if not isinstance(employee_id, str) or not ID_RE.fullmatch(employee_id):
        return "Invalid employee id. Expected the format E123."
    requester = os.environ.get("HELPDESK_REQUESTER", "")
    hr_admin = os.environ.get("HR_ADMIN_ID", "E001")
    if requester != employee_id and requester != hr_admin:
        return "Not authorized: you can only look up your own records."
    return None


def _query(sql: str, params: tuple) -> list[tuple]:
    with psycopg.connect(os.environ["MCP_DATABASE_URL"], autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only = on")
        return conn.execute(sql, params).fetchall()


@mcp.tool()
def get_leave_balance(employee_id: str, leave_type: str | None = None) -> dict:
    """Leave balance for one employee: entitled, used and remaining days per leave type.
    employee_id looks like E102. leave_type is optional: casual, sick or earned."""
    if err := _check(employee_id):
        return {"error": err}
    if leave_type is not None and leave_type.lower() not in LEAVE_TYPES:
        return {"error": f"Unknown leave_type. Use one of {sorted(LEAVE_TYPES)}."}
    sql = (
        "SELECT leave_type, entitled, used, entitled - used AS remaining "
        "FROM leave_balances WHERE employee_id = %s"
    )
    params: tuple = (employee_id,)
    if leave_type:
        sql += " AND leave_type = %s"
        params += (leave_type.lower(),)
    rows = _query(sql + " ORDER BY leave_type LIMIT 10", params)
    if not rows:
        return {"error": f"Employee {employee_id} not found."}
    return {
        "employee_id": employee_id,
        "balances": [
            {"leave_type": t, "entitled": e, "used": u, "remaining": r} for t, e, u, r in rows
        ],
    }


@mcp.tool()
def get_employee_profile(employee_id: str) -> dict:
    """Profile for one employee: name, department, role, manager and contact details."""
    if err := _check(employee_id):
        return {"error": err}
    rows = _query(
        "SELECT employee_id, name, department, role, manager_id, work_email, phone, personal_email "
        "FROM employees WHERE employee_id = %s LIMIT 1",
        (employee_id,),
    )
    if not rows:
        return {"error": f"Employee {employee_id} not found."}
    keys = ["employee_id", "name", "department", "role", "manager_id", "work_email", "phone", "personal_email"]
    return dict(zip(keys, rows[0]))


if __name__ == "__main__":
    mcp.run(transport="stdio")
