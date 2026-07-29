# ADR-002: Keep final lending authority outside the model

- Status: Accepted
- Date: 2026-07-29
- Owners: Credit Policy, Model Risk and Compliance

## Context

Creditworthiness assessment can materially affect individuals. Model output must not be
confused with a final legal or business decision.

## Decision

The model service returns only a recommendation and evidence. `REFER` and
`DECLINE_RECOMMENDATION` always require authorized human review. The reference service has
no connector that can book a loan, send a notice or update a core banking system.

## Consequences

- Human rationale and overrides require a separate audit event in production.
- The system can be tested in shadow mode without affecting applicants.
- Legal disclosure and adverse-action requirements remain downstream governance obligations.
- Human oversight must be meaningful, trained and empowered rather than ceremonial.
