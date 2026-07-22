# Hardware BOM

## Scope

FEAT-003 is a hardware integration reference only. It intentionally ignores MAVLink / Mission Planner export and does not require ArduRover firmware development.

## Controller Stack

- Pixhawk 2.4.8 / PIX 32-bit APM-compatible controller: primary Phase 1 ArduRover controller.
- Raspberry Pi 4/5 or Pi Zero 2 W: optional companion computer for later logging, UI, camera, or network bridge. It must not be the only safety path.
- 433/915 MHz telemetry radio: preferred field telemetry under wet cucumber canopy.
- RC transmitter/receiver: required manual override and mode control.

## Required Prototype BOM

- Flight controller: Pixhawk 2.4.8 or PIX 32-bit kit, 1x.
- Telemetry: 3DR-style 433/915 MHz radio pair, 1x pair.
- RC control: transmitter/receiver with mode switch and override/kill channel, 1x.
- GPS/compass/RTK: Pixhawk-compatible module, 1x.
- Waterproof ultrasonic sensors: front, left, right, 3x total; JSN-SR04T or GY-US42-class alternatives.
- Pump: 12/24 V diaphragm pump sized to selected nozzles and pressure, 1x.
- Valves: 12/24 V normally-closed solenoid valves, left and right, 2x.
- Drivers: MOSFET/relay driver channels with flyback protection; opto-isolation preferred, 3x channels minimum.
- Liquid level: tank float switch or non-contact level sensor, 1x.
- Pressure sensing: water pressure transducer or high/low pressure switches, 1x.
- Safety: physical emergency stop cutting motor and pump/valve power independently of Pixhawk/RPi, 1x.
- Power: fused battery distribution, Pixhawk BEC/power module, Raspberry Pi buck supply if used, separate pump/valve fused rail.
- Fluid path: tank fittings, filter, pressure gauge, tubing, check valves, nozzle holders, left/right nozzles.

## Buying Notes

- Prefer normally-closed valves so loss of power means spray off.
- Select pump pressure/flow after nozzle choice; avoid oversizing before nozzle tests.
- Use waterproof connectors and strain relief near crop rows.
- Keep pump/valve power wiring physically separated from GPS, compass, RC, and telemetry wiring.
- Do not commit real farm coordinates, Wi-Fi passwords, telemetry IDs, or hardware credentials.
