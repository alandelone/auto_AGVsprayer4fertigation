# 03 Execution

## Ordered Tasks

1. Add machine-readable hardware BOM/pinout contract.
2. Add human-readable hardware BOM doc.
3. Add Pixhawk/Raspberry Pi/pump/valve pinout doc.
4. Add deterministic validator and wire it into `scripts/check-gate.sh`.
5. Run gate checks and update FEAT-003 only after PASS evidence exists.

## Files Expected To Change

- `feature-list.json`
- `hardware/bom-pinout.v0.json`
- `docs/hardware-bom.md`
- `docs/pixhawk-rpi-pump-valve-pinout.md`
- `scripts/validate-hardware-pinout.py`
- `scripts/check-gate.sh`
- `stage-gates/active/FEAT-003/*.md`
- `active-session/HANDOFF.md`
- `active-session/progress.log`

## Definition Of Done

- BOM includes required controller, sensing, actuator, power, safety, and fluid-path categories.
- Pinout includes Pixhawk/RPi/RC/telemetry/rangefinder/pump/valve/liquid/pressure/E-stop signals.
- Documents explicitly state no ArduRover firmware changes for FEAT-003.
- `bash scripts/check-gate.sh` succeeds.
