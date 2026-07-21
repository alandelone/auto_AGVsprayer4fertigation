# Testing Rules

- Tests must be deterministic and runnable without live hardware by default.
- Use `test-fixtures/` for seed data and simulated device responses.
- Cover safety limits, invalid sensor values, route edge cases, and actuator bounds.
- Record verification evidence in the active feature's `04-verification.md`.
- A feature is passable only when `scripts/check-gate.sh` succeeds.
