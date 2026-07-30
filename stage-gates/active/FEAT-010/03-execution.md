# 03 Execution — FEAT-010 SITL Fault Recovery, Resume Policy, and Telemetry Log

## Goal

Convert the FEAT-010 design into an implementation contract that can be completed in later focused runs without relying on chat memory.

## Ordered tasks

1. Create `sitl/fault-recovery-telemetry.v0.json` with recovery-policy configuration, telemetry schema requirements, and deterministic scenarios:
   - obstacle fault triggers HOLD, clears, resumes at the first unsprayed segment, and completes the mission,
   - canopy or sensor degradation enters HOLD or bounded recovery according to FEAT-009 confidence state,
   - duplicate-spray replay attempt is suppressed and recorded,
   - unrecoverable sensor fault or timeout remains HOLD/aborts with outputs off,
   - stale clear event or missing acknowledgement blocks resume,
   - telemetry missing a required event or field fails validation.
2. Implement `scripts/validate-fault-recovery-telemetry.py` to load the contract, validate required fields, compute recovery/resume decisions, enforce actuator safety, enforce spray-ledger no-duplicate behavior, and verify telemetry completeness.
3. Add `docs/fault-recovery-telemetry.md` documenting the state machine, resume rules, duplicate-spray ledger, actuator safety, telemetry schema, and SITL/companion integration path.
4. Wire the validator into `scripts/check-gate.sh` after the contract and validator exist.
5. Run targeted checks and full gate, then paste actual command/output evidence into `04-verification.md`.
6. Only after the full gate passes, run `python scripts/update-feature.py feature-list.json` to mark FEAT-010 passing.

## Files expected to change

- `stage-gates/active/FEAT-010/01-discovery.md`
- `stage-gates/active/FEAT-010/02-tech-design.md`
- `stage-gates/active/FEAT-010/03-execution.md`
- `stage-gates/active/FEAT-010/04-verification.md`
- `sitl/fault-recovery-telemetry.v0.json`
- `scripts/validate-fault-recovery-telemetry.py`
- `docs/fault-recovery-telemetry.md`
- `docs/project-index.md`
- `scripts/check-gate.sh`
- `feature-list.json` — do not hand-edit `passes`; use `scripts/update-feature.py` only after the gate passes.
- `active-session/progress.log`
- `active-session/HANDOFF.md`

## Definition of done

- All required FEAT-010 gate files exist.
- JSON contract covers successful resume, duplicate-spray suppression, unrecoverable HOLD/abort, stale-clear or missing-ack rejection, and telemetry completeness checks.
- Validator rejects malformed contracts and fails on mismatched expected decisions or incomplete telemetry.
- Documentation has concrete state, resume, spray-ledger, and telemetry semantics with no unfinished-marker content.
- Full gate passes with `CHECK_GATE_EXIT=0`.
- `04-verification.md` contains actual command/output pairs, not projected output.
- `feature-list.json` marks FEAT-010 `passes=true` only via `scripts/update-feature.py` after the gate passes.

## Validation commands

```bash
python -m py_compile scripts/validate-fault-recovery-telemetry.py
python scripts/validate-fault-recovery-telemetry.py sitl/fault-recovery-telemetry.v0.json
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```

## Implementation workflow note

The remaining FEAT-010 implementation has multiple independent artifacts. Follow the repository subagent/code-review discipline when implementation begins: split contract, validator, and documentation/gate wiring into reviewed components or use a parallel-session handoff with checkpoints.
