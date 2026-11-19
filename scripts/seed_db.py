"""Create schema and seed employee data (idempotent: drops employees/leave tables)."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main() -> None:
    url = os.environ["DATABASE_URL"]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute((ROOT / "data/db/schema.sql").read_text(encoding="utf-8"))
        conn.execute((ROOT / "data/db/seed.sql").read_text(encoding="utf-8"))
        n = conn.execute("SELECT count(*) FROM employees").fetchone()[0]
        print(f"Seeded {n} employees.")


if __name__ == "__main__":
    main()
