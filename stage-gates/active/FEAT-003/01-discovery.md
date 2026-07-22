# 01 Discovery

## Goal

Define the non-firmware hardware BOM and wiring boundary for the cucumber AGV sprayer/fertigation prototype.

## User Direction

- Ignore MAVLink / Mission Planner export for now.
- Prioritize hardware BOM and Pixhawk/Raspberry Pi/pump/valve pinout.
- Keep this work separate from ArduRover firmware development because it does not affect firmware dev.

## Success Criteria

- Produce a purchase/planning BOM for Pixhawk, optional Raspberry Pi, telemetry, RC, sensors, pump, valves, drivers, power, and safety hardware.
- Produce a prototype pinout that maps sensors and spray actuators to Pixhawk/RPi/control interfaces.
- State voltage, isolation, emergency stop, and no-direct-load rules.
- Add deterministic validation so future edits do not remove required safety categories or signals.

## Out Of Scope

- MAVLink / Mission Planner route export.
- ArduRover firmware edits.
- Real farm coordinates, credentials, or private hardware secrets.
