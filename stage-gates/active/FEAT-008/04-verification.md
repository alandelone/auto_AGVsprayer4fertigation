# 04 Verification — FEAT-008

STATUS: FAIL

## Current verification state

FEAT-008 is intentionally open. Stage-gate contracts have been created and the active feature pointer has moved to FEAT-008, but the deterministic preflight/dosing contract and validator are not implemented yet.

## Commands run

```bash
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```

Output:

```text
Initializing auto_AGVsprayer4fertigation workspace...
No build or test toolchain is configured yet.
Add setup commands here when source code is introduced.
FAIL: verification gate status must be PASS
CHECK_GATE_EXIT=1
```

## Repair suggestions

- Add `sitl/preflight-dosing.v0.json`.
- Add `scripts/validate-preflight-dosing.py`.
- Wire the validator into `scripts/check-gate.sh`.
- Replace this failing evidence with actual passing command output before marking FEAT-008 passing.
