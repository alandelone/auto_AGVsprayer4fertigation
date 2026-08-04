# 04 Verification — FEAT-010 SITL Fault Recovery, Resume Policy, and Telemetry Log

STATUS: PASS

FEAT-010 artifacts are validated by targeted syntax/contract checks and the full repository gate. The captured command/output pairs below are from this branch inside `/home/ubuntu/agents/evergreen4/auto_AGVsprayer4fertigation`.

## Targeted validation evidence

### Gate script shell syntax

```bash
bash -n scripts/check-gate.sh; code=$?; echo BASH_N_EXIT=$code
```

Output:

```text
BASH_N_EXIT=0
```

### Fault recovery telemetry validator syntax

```bash
python -m py_compile scripts/validate-fault-recovery-telemetry.py; code=$?; echo PY_COMPILE_EXIT=$code
```

Output:

```text
PY_COMPILE_EXIT=0
```

### Fault recovery telemetry contract validation

```bash
python scripts/validate-fault-recovery-telemetry.py sitl/fault-recovery-telemetry.v0.json; code=$?; echo VALIDATOR_EXIT=$code
```

Output:

```text
PASS: fault recovery telemetry contract validated
Validated scenarios: 5 (3 complete, 3 hold-entered, 2 resume/continue decisions)
Outcome counts: MISSION_COMPLETE_AFTER_RECOVERY=1 BOUNDED_DEAD_RECKONING_COMPLETE=1 DUPLICATE_SUPPRESSED_COMPLETE=1 MISSION_ABORTED=1 RESUME_BLOCKED=1
Duplicate suppression events: 1
Negative telemetry cases: 2
Recovery policy: max_clear_age=2.0s max_hold=15.0s safe_latency=200ms
VALIDATOR_EXIT=0
```

## Full repository gate evidence

```bash
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```

Output:

```text
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
PASS: fault recovery telemetry contract validated
Validated scenarios: 5 (3 complete, 3 hold-entered, 2 resume/continue decisions)
Outcome counts: MISSION_COMPLETE_AFTER_RECOVERY=1 BOUNDED_DEAD_RECKONING_COMPLETE=1 DUPLICATE_SUPPRESSED_COMPLETE=1 MISSION_ABORTED=1 RESUME_BLOCKED=1
Duplicate suppression events: 1
Negative telemetry cases: 2
Recovery policy: max_clear_age=2.0s max_hold=15.0s safe_latency=200ms
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
