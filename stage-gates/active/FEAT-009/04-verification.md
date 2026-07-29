# 04 Verification — FEAT-009 SITL Position Confidence + Canopy Fallback

STATUS: PASS

FEAT-009 implementation artifacts are complete for deterministic SITL position confidence validation: the scenario contract, validator, fallback documentation, and repo gate wiring are present and exercised with captured command output below.

## Command/output evidence

### Targeted validator and documentation checks

```bash
python -m py_compile scripts/validate-position-confidence.py && python scripts/validate-position-confidence.py sitl/position-confidence.v0.json && python -c "from pathlib import Path; p=Path('docs/position-confidence-fallback.md'); text=p.read_text(encoding='utf-8'); required=['## Scope','## Inputs and Units','## Configured Thresholds','## Decision States','## Actuator Safety Behavior','## SITL / Companion Integration Path']; missing=[h for h in required if h not in text]; forbidden=[w for w in ['TBD','TODO','placeholder','Expected output'] if w.lower() in text.lower()]; index=Path('docs/project-index.md').read_text(encoding='utf-8'); print(f'DOC_EXISTS={p.exists()} DOC_BYTES={p.stat().st_size}'); print('DOC_REQUIRED_HEADINGS_OK' if not missing else 'DOC_MISSING_HEADINGS='+','.join(missing)); print('DOC_PLACEHOLDER_CHECK_OK' if not forbidden else 'DOC_FORBIDDEN_TERMS='+','.join(forbidden)); print('DOC_INDEX_OK' if 'docs/position-confidence-fallback.md' in index else 'DOC_INDEX_MISSING'); raise SystemExit(1 if missing or forbidden or 'docs/position-confidence-fallback.md' not in index else 0)"
```

Output:

```text
PASS: position confidence contract validated
Validated scenarios: 6 (2 continue, 4 safe_hold)
Decision counts: RTK_CONFIDENT=1 DEAD_RECKONING_ACTIVE=1 SAFE_HOLD=4
Mission spray segments: 2
Fallback budget: 6.0s / 1.500m
DOC_EXISTS=True DOC_BYTES=6072
DOC_REQUIRED_HEADINGS_OK
DOC_PLACEHOLDER_CHECK_OK
DOC_INDEX_OK
```

### Full repository gate

```bash
git status --short --branch && bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```

Output:

```text
## feat/sitl-position-confidence...origin/feat/sitl-position-confidence
 M stage-gates/active/FEAT-009/04-verification.md
Initializing auto_AGVsprayer4fertigation workspace...
No build or test toolchain is configured yet.
Add setup commands here when source code is introduced.
PASS: preflight dosing contract validated
Validated scenarios: 3 (1 safe, 2 blocked)
Mission spray segments: 2
Reference target_flow_lpm: 0.600
PASS: position confidence contract validated
Validated scenarios: 6 (2 continue, 4 safe_hold)
Decision counts: RTK_CONFIDENT=1 DEAD_RECKONING_ACTIVE=1 SAFE_HOLD=4
Mission spray segments: 2
Fallback budget: 6.0s / 1.500m
Gate check passed
Validated route/spray/safety contracts: routes/examples/cucumber-row-route.example.json
Mission contract simulation PASS: routes/examples/cucumber-row-route.example.json
- ROW_ENTRY entry_transit: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
- SPRAY_ON row_01_left_spray: spray=LEFT speed=0.25 outputs={'pump': True, 'left_valve': True, 'right_valve': False}
- SPRAY_TRANSITION OFF->LEFT at row_01_left_spray
- FAULT_STOP front_obstacle during row_01_left_spray: mode=HOLD outputs={'pump': False, 'left_valve': False, 'right_valve': False} operator_review_required=True
- SPRAY_TRANSITION LEFT->OFF at row_01_exit_off
- ROW_EXIT row_01_exit_off: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
- MISSION_END return_to_hold: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
Validated hardware BOM/pinout contract: hardware/bom-pinout.v0.json
Validated bench ratings contract: hardware/bench-test-ratings.v0.json margin=3.3x
Validated bench procedure contract: hardware/bench-test-procedure.v0.json tests=8
Validated Pixhawk actuator mapping: hardware/pixhawk-actuator-mapping.v0.json
Validated ArduRover parameter export: hardware/pixhawk-ardurover-sprayer.param
ACTUATOR_OUTPUTS=AUX1,AUX2,AUX3,AUX4,AUX5
PARAMETERS=BRD_PWM_COUNT,SERVO9_FUNCTION,SERVO9_MIN,SERVO9_MAX,RELAY1_PIN,RELAY1_DEFAULT,RELAY2_PIN,RELAY2_DEFAULT,RELAY3_PIN,RELAY3_DEFAULT,RELAY4_PIN,RELAY4_DEFAULT
MISSION_EXPORT_VALIDATION_OK
SOURCE_ITEMS=7 EXPORT_ITEMS=28 WAYPOINTS=6
COMMAND_COUNTS NAV_WAYPOINT=6 DO_CHANGE_SPEED=6 DO_SET_RELAY=12 DO_SET_SERVO=4
SAFETY_TRANSITIONS=4 ACTUATOR_COMMANDS=16
CHECK_GATE_EXIT=0
```
