# FEAT-005 Technical Design

## Design

Add a machine-readable bench-test procedure contract and a human procedure doc. The procedure orders tests from safest to riskiest: dry inspection, e-stop, prime/leak, pressure limits, low-liquid, zone valves, catch-cup flow, and fault-safe state.

## Files

- `hardware/bench-test-procedure.v0.json`
- `docs/water-only-bench-test-procedure.md`
- `templates/bench-test-log.template.json`
- `scripts/validate-bench-procedure.py`

## Verification Strategy

Validator confirms all required test IDs exist, water-only constraints are explicit, stop conditions/forbidden actions exist, catch-cup acceptance is bounded, and log template aligns with the procedure.
