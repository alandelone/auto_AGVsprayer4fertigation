# FEAT-006 Discovery: ArduRover Pixhawk Actuator Mapping & Parameter Export

## Goal

Define the exact Pixhawk ArduRover parameter mappings and output definitions for driving pump PWM, spray valves, agitation, and E-stop cutoff channels without logic conflict.

## Requirements

1. **SERVO / RELAY Assignments:**
   - Servo Channel 9 (`SERVO9_FUNCTION`): Pump PWM Speed Control (`SERVO9_MIN=1000`, `SERVO9_MAX=2000`).
   - Relay 1 (`RELAY1_PIN` / `SERVO10_FUNCTION`): Left Spray Valve Relay (Pixhawk AUX Pin 2 / GPIO 51).
   - Relay 2 (`RELAY2_PIN` / `SERVO11_FUNCTION`): Right Spray Valve Relay (Pixhawk AUX Pin 3 / GPIO 52).
   - Relay 3 (`RELAY3_PIN` / `SERVO12_FUNCTION`): Tank Agitation Pump/Valve Relay (Pixhawk AUX Pin 4 / GPIO 53).
   - Relay 4 (`RELAY4_PIN` / `SERVO13_FUNCTION`): Emergency Stop Physical Cutoff Relay (Pixhawk AUX Pin 5 / GPIO 54).

2. **Parameter File Dump:**
   - Produce standard ArduRover parameter file `hardware/pixhawk-ardurover-sprayer.param` ready for Mission Planner / QGroundControl parameter upload.

3. **Validation:**
   - Provide a deterministic validator `scripts/validate-pixhawk-mapping.py` to confirm mapping consistency.
