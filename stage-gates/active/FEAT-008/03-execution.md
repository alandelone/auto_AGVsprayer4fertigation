# 03 Execution — FEAT-008

## Goal

Convert the FEAT-008 design into a small deterministic implementation contract before any SITL/companion-control code is added.

## Ordered tasks

1. Create `sitl/preflight-dosing.v0.json` with explicit preflight checks, dosing inputs, expected outcomes, and at least one blocked unsafe condition.
2. Implement `scripts/validate-preflight-dosing.py` using Python standard library only.
3. Wire `scripts/check-gate.sh` to run the new validator.
4. Add `docs/preflight-dosing.md` describing dry-run/SITL use, units, safety decisions, and calibration interpretation.
5. Run targeted validation and full gate; paste actual output into `04-verification.md`.
6. Only after the full gate succeeds, run `python scripts/update-feature.py feature-list.json` to mark FEAT-008 passing.

## Files expected to change

- `feature-list.json` — active pointer changed from FEAT-007 to FEAT-008 only; do not hand-edit `passes`.
- `stage-gates/active/FEAT-008/01-discovery.md`
- `stage-gates/active/FEAT-008/02-tech-design.md`
- `stage-gates/active/FEAT-008/03-execution.md`
- `stage-gates/active/FEAT-008/04-verification.md`
- `sitl/preflight-dosing.v0.json`
- `scripts/validate-preflight-dosing.py`
- `scripts/check-gate.sh`
- `docs/preflight-dosing.md`

## Definition of done

- FEAT-008 gate files exist and verification has `STATUS: PASS` only after actual successful command output is captured.
- Preflight validator validates both safe and unsafe deterministic scenarios.
- Full repo gate exits 0.
- FEAT-008 `passes` is updated only by `python scripts/update-feature.py feature-list.json` after gate success.

## Validation commands

```bash
python scripts/validate-preflight-dosing.py
```

```bash
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```
