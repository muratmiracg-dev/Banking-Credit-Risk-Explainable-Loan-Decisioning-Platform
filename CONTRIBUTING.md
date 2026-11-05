# Contributing

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python scripts/run_pipeline.py
ruff check src tests scripts
ruff format --check src tests scripts
pytest
```

## Change requirements

- Preserve the recommendation-only safety boundary.
- Do not add real or sensitive data.
- Document model, feature, threshold and monitoring changes.
- Add tests for new behavior.
- Keep `requirements.txt` exact. When bumping a library, rerun the pipeline and commit the
  regenerated artifacts in the same change; CI compares them with a fresh rebuild.
- Rebuild deterministic artifacts when analytical code changes.
- Update the model card, validation evidence and risk register for material model changes.
- Do not weaken fairness findings or disclaimers to improve presentation.

## Commit style

Use short imperative subjects, for example:

- `Add temporal calibration monitor`
- `Document policy override control`
- `Harden scoring request validation`
