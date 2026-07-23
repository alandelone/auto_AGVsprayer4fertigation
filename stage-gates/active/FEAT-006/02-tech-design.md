# FEAT-006 Technical Design: Pixhawk ArduRover Parameter Export & Mapping Contract

## Architecture

- **Machine-Readable Mapping Contract:** `hardware/pixhawk-actuator-mapping.v0.json` owns channel definitions, logic states, default fail-safe positions, and parameter key-value pairs.
- **ArduRover Parameter File:** `hardware/pixhawk-ardurover-sprayer.param` formats the mapping as standard ArduPilot key-value parameters (`PARAM_NAME,VALUE`).

## Pinout & Parameter Table

| Parameter Name | Value | Purpose |
| :--- | :--- | :--- |
| `BRD_PWM_COUNT` | `4` | AUX1-AUX4 configured for PWM/Relay functionality |
| `SERVO9_FUNCTION` | `0` | Disabled default PWM, reserved for Pump Speed Control |
| `SERVO9_MIN` | `1000` | Minimum pump PWM pulse (OFF / 0 RPM) |
| `SERVO9_MAX` | `2000` | Maximum pump PWM pulse (100% Speed / 60 PSI) |
| `RELAY1_PIN` | `51` | Pixhawk AUX Out 2 mapped to Left Spray Valve Relay |
| `RELAY1_DEFAULT` | `0` | Default OFF state at boot |
| `RELAY2_PIN` | `52` | Pixhawk AUX Out 3 mapped to Right Spray Valve Relay |
| `RELAY2_DEFAULT` | `0` | Default OFF state at boot |
| `RELAY3_PIN` | `53` | Pixhawk AUX Out 4 mapped to Agitation Valve Relay |
| `RELAY3_DEFAULT` | `0` | Default OFF state at boot |
| `RELAY4_PIN` | `54` | Pixhawk AUX Out 5 mapped to E-Stop Cutoff Relay |
| `RELAY4_DEFAULT` | `1` | Default Active High E-Stop Closed signal |

## Test Plan

- Execute `python scripts/validate-pixhawk-mapping.py` to verify:
  1. JSON mapping file `hardware/pixhawk-actuator-mapping.v0.json` exists and is valid.
  2. `.param` file `hardware/pixhawk-ardurover-sprayer.param` matches the JSON parameter definitions.
  3. No channel conflicts exist between pump PWM, valves, agitation, and E-stop.
