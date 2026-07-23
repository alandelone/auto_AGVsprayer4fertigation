# FEAT-007 Technical Design: Mission Export Contract and ArduPilot Outputs

## Architecture

- **Source Contract:** `missions/cucumber-row-mission.v0.json` owns the synthetic route, speed targets, spray states, and actuator transition points.
- **Exporter:** `scripts/export-mission-files.py` reads the source contract plus `hardware/pixhawk-actuator-mapping.v0.json` and writes both mission formats.
- **Artifacts:**
  - `missions/exports/cucumber-row-mission.plan`
  - `missions/exports/cucumber-row-mission.waypoints`
- **Validator:** `scripts/validate-mission-exports.py` parses source and generated artifacts to verify command consistency.

## Command Mapping

| Function | ArduPilot command | Channel / relay | OFF value | ON value |
| :--- | :--- | :--- | :--- | :--- |
| Pump PWM | `MAV_CMD_DO_SET_SERVO` (`183`) | Servo 9 | `1000` | dosing PWM from route contract |
| Left valve | `MAV_CMD_DO_SET_RELAY` (`181`) | Relay 1 | `0` | `1` |
| Right valve | `MAV_CMD_DO_SET_RELAY` (`181`) | Relay 2 | `0` | `1` |
| Agitation | `MAV_CMD_DO_SET_RELAY` (`181`) | Relay 3 | `0` | optional `1` during spray segments |

## Output Rules

1. Both mission formats must start with explicit actuator-safe OFF commands before the first navigation waypoint.
2. Every spray segment must include pump PWM ON and the selected valve relay ON before/at row spray entry.
3. Every row exit must include valve OFF and pump PWM OFF before the next non-spray transit segment.
4. Generated `.waypoints` must use ArduPilot WPL 110 header and stable numeric columns.
5. Generated `.plan` must use a deterministic JSON structure compatible with QGroundControl mission items.
6. No exported artifact may contain private field coordinates; the example must remain synthetic/test-only.

## Test Plan

Run:

```bash
python scripts/export-mission-files.py
python scripts/validate-mission-exports.py
bash init.sh && bash scripts/check-gate.sh
```

The final verification gate must paste actual captured command output and set `STATUS: PASS` only after the validator and repo gate succeed.
