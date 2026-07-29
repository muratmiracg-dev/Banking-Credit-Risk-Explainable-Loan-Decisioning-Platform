# Human oversight standard

## Meaningful review

A reviewer must have enough time, evidence, competence and authority to challenge the model.
Simply clicking “approve” does not satisfy this design.

## Minimum reviewer evidence

- Validated application fields and data-quality state
- Model version and policy version
- PD, score, risk band and recommendation
- Top reason codes and explanation limitation
- Relevant policy exceptions
- Monitoring or model-health warnings

## Reviewer actions

- Confirm recommendation
- Request additional evidence
- Refer to a specialist
- Override with a documented reason
- Decline to act if the model or data are unreliable

## Required audit event

A production audit record should contain request ID, timestamps, model and policy versions,
inputs or approved input hash, model output, reviewer identity, action, rationale, override
code and disclosure reference.

## Escalation triggers

- Missing or contradictory application evidence
- Amber or red model monitoring state
- Novel category or out-of-range input
- Suspected discrimination or complaint
- Material policy exception
- Service, data or explanation incident
