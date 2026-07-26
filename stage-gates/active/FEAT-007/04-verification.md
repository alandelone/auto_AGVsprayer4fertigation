# FEAT-007 Verification

## Verification Output

STATUS: PASS

## Evidence

### Exporter + validator

```bash
python scripts/export-mission-files.py && python scripts/validate-mission-exports.py
```

Output:

```text
EXPORTED_QGC_PLAN=missions/exports/cucumber-row-mission.plan
EXPORTED_ARDUPILOT_WPL110=missions/exports/cucumber-row-mission.waypoints
MISSION_EXPORT_ITEMS=28 WAYPOINTS=6 ACTUATOR_COMMANDS=16
MISSION_EXPORT_VALIDATION_OK
SOURCE_ITEMS=7 EXPORT_ITEMS=28 WAYPOINTS=6
COMMAND_COUNTS NAV_WAYPOINT=6 DO_CHANGE_SPEED=6 DO_SET_RELAY=12 DO_SET_SERVO=4
SAFETY_TRANSITIONS=4 ACTUATOR_COMMANDS=16
```

### Generated QGC `.plan` JSON and ArduPilot WPL 110 smoke check

```bash
python -m json.tool missions/exports/cucumber-row-mission.plan >/tmp/feat007-plan-jsoncheck.out && python - <<'PY'
from pathlib import Path
wpl = Path('missions/exports/cucumber-row-mission.waypoints')
lines = wpl.read_text(encoding='utf-8').splitlines()
assert lines[0] == 'QGC WPL 110'
assert len(lines) == 29, len(lines)
cols = [line.split('\t') for line in lines[1:]]
assert all(len(row) == 12 for row in cols)
commands = [int(row[3]) for row in cols]
assert commands.count(16) == 6
assert commands.count(178) == 6
assert commands.count(181) == 12
assert commands.count(183) == 4
print(f'EXPORT_SMOKE_OK wpl_lines={len(lines)} commands_16={commands.count(16)} commands_178={commands.count(178)} commands_181={commands.count(181)} commands_183={commands.count(183)}')
PY
```

Output:

```text
EXPORT_SMOKE_OK wpl_lines=29 commands_16=6 commands_178=6 commands_181=12 commands_183=4
```

### Full repository gate

```bash
bash init.sh && bash scripts/check-gate.sh
```

Output captured before marking FEAT-007 passing in `feature-list.json`:

```text
Initializing auto_AGVsprayer4fertigation workspace...
No build or test toolchain is configured yet.
Add setup commands here when source code is introduced.
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
