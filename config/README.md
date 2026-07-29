# Configuration

`project.yaml` is the visible source of truth for:

- portfolio seed and time windows;
- champion/challenger names and validation gates;
- protected-attribute exclusion;
- approve and refer PD thresholds;
- LGD and score-mapping assumptions;
- monitoring warning and critical levels;
- the synthetic-only and production-disabled safety flags.

Threshold or model changes require regenerated artifacts, tests, validation evidence and
governance approval.
