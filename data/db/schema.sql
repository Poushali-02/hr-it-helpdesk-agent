CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS leave_balances;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id    TEXT PRIMARY KEY CHECK (employee_id ~ '^E[0-9]{3}$'),
    name           TEXT NOT NULL,
    department     TEXT NOT NULL,
    role           TEXT NOT NULL,
    manager_id     TEXT REFERENCES employees(employee_id),
    work_email     TEXT NOT NULL,
    phone          TEXT,
    personal_email TEXT,
    pan            TEXT
);

CREATE TABLE leave_balances (
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    leave_type  TEXT NOT NULL CHECK (leave_type IN ('casual','sick','earned')),
    entitled    INT  NOT NULL,
    used        INT  NOT NULL,
    PRIMARY KEY (employee_id, leave_type)
);

CREATE TABLE IF NOT EXISTS policy_chunks (
    id        SERIAL PRIMARY KEY,
    doc       TEXT NOT NULL,
    section   TEXT NOT NULL,
    content   TEXT NOT NULL,
    embedding vector(384) NOT NULL
);
CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks USING hnsw (embedding vector_cosine_ops);

-- Read-only role used by the MCP server
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'helpdesk_ro') THEN
        CREATE ROLE helpdesk_ro LOGIN PASSWORD 'helpdesk_ro';
    END IF;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM helpdesk_ro;
GRANT CONNECT ON DATABASE helpdesk TO helpdesk_ro;
GRANT USAGE ON SCHEMA public TO helpdesk_ro;
GRANT SELECT ON employees, leave_balances TO helpdesk_ro;
