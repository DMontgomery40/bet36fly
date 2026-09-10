.PHONY: setup brain fetch train serve verify

setup:
	uv sync
	cd web && npm ci

brain:
	.venv/bin/python scripts/prepare_connectome.py

fetch:
	.venv/bin/python scripts/fetch_sports.py

train:
	.venv/bin/python -m bet36fly.experiment

serve:
	.venv/bin/python -m uvicorn bet36fly.server:app --host 127.0.0.1 --port 8765

verify:
	.venv/bin/python -m pytest -q
	.venv/bin/ruff check bet36fly tests scripts
	cd web && npm test
	cd web && npm run build
