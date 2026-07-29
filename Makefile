.PHONY: install pipeline test lint run-api verify clean

install:
	python -m pip install -e ".[dev,reporting]"

pipeline:
	PYTHONPATH=src MPLCONFIGDIR=/tmp/mpl-credit-risk python scripts/run_pipeline.py

test:
	PYTHONPATH=src python -m pytest

lint:
	python -m ruff check src tests scripts
	python -m ruff format --check src tests scripts

run-api:
	CREDIT_RISK_ROOT=$$(pwd) uvicorn credit_risk.api:app --app-dir src --host 0.0.0.0 --port 8000

verify: pipeline lint test
	python scripts/verify_artifacts.py

clean:
	find src tests scripts -type d -name __pycache__ -prune -exec rm -r {} +
