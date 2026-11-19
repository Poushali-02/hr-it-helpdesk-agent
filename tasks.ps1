# Windows fallback for the Makefile: .\tasks.ps1 up | seed | ingest | ask "question" [E102] | eval | test | down
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Task,
    [Parameter(Position = 1)][string]$Q,
    [Parameter(Position = 2)][string]$As = "E102"
)
switch ($Task) {
    "up"     { docker compose up -d --wait }
    "down"   { docker compose down }
    "seed"   { uv run python scripts/seed_db.py }
    "ingest" { uv run python -m helpdesk.ingest }
    "ask"    { uv run python -m helpdesk ask $Q --as $As }
    "eval"   { uv run python scripts/run_eval.py }
    "test"   { uv run pytest }
    default  { Write-Error "Unknown task: $Task" }
}
