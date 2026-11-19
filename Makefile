.PHONY: up down seed ingest ask eval test

up:
	docker compose up -d --wait

down:
	docker compose down

seed:
	uv run python scripts/seed_db.py

ingest:
	uv run python -m helpdesk.ingest

ask:
	uv run python -m helpdesk ask "$(Q)" --as $(or $(AS),E102)

eval:
	uv run python scripts/run_eval.py

test:
	uv run pytest
