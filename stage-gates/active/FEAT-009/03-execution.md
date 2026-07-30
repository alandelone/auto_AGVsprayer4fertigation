# 03 Execution — FEAT-009 SITL Position Confidence + Canopy Fallback

## Goal

Convert the FEAT-009 design into an implementation contract that can be completed in a later focused run without relying on chat memory.

## Ordered tasks

1. Create `sitl/position-confidence.v0.json` with threshold configuration and deterministic scenarios:
   - nominal RTK confident mission segment,
   - canopy GPS degradation with bounded dead reckoning accepted,
   - GPS stale sample rejected to HOLD,
   - IMU/odometer disagreement rejected to HOLD,
   - ultrasonic row cue invalid rejected to HOLD,
   - fallback duration or distance budget expired rejected to HOLD.
2. Implement `scripts/validate-position-confidence.py` to load the contract, validate schema-like required fields, compute decisions, and compare expected outcomes.
3. Add `docs/position-confidence-fallback.md` documenting states, thresholds, actuator safety, and SITL integration path.
4. Wire the validator into `scripts/check-gate.sh`.
5. Run targeted checks and full gate, then paste actual command/output evidence into `04-verification.md`.
6. Only after the full gate passes, run `python scripts/update-feature.py feature-list.json` to mark FEAT-009 passing.

## Files expected to change

- `feature-list.json` — active pointer only while FEAT-009 is in progress; do not hand-edit `passes`.
- `stage-gates/active/FEAT-009/01-discovery.md`
- `stage-gates/active/FEAT-009/02-tech-design.md`
- `stage-gates/active/FEAT-009/03-execution.md`
- `stage-gates/active/FEAT-009/04-verification.md`
- `sitl/position-confidence.v0.json`
- `scripts/validate-position-confidence.py`
- `docs/position-confidence-fallback.md`
- `scripts/check-gate.sh`
- `active-session/progress.log`
- `active-session/HANDOFF.md`

## Definition of done

- All required FEAT-009 gate files exist.
- JSON contract has enough positive/negative coverage for RTK confidence, bounded fallback, and each unsafe stop path.
- Validator rejects malformed contracts and fails on mismatched expected decisions.
- Full gate passes with `CHECK_GATE_EXIT=0`.
- `04-verification.md` contains actual command/output pairs, not expected output.
- `feature-list.json` marks FEAT-009 `passes=true` only via `scripts/update-feature.py` after the gate passes.

## Validation commands

```bash
python -m py_compile scripts/validate-position-confidence.py
python scripts/validate-position-confidence.py sitl/position-confidence.v0.json
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```
