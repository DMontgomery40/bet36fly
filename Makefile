.PHONY: setup brain fetch train serve serve-verify verify

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

serve-verify:
	PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m uvicorn bet36fly.server:create_verification_app --factory --host 127.0.0.1 --port 8765

verify:
	.venv/bin/python -m pytest -q
	.venv/bin/ruff check bet36fly tests scripts
	cd web && npm test
	cd web && npm run build

.PHONY: experiment-v2
experiment-v2:
	.venv/bin/python -m bet36fly.experiment_v2 --protocol configs/experiment-v2.json
