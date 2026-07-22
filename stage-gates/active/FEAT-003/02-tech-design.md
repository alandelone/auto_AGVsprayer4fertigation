# 02 Tech Design

## Architecture Boundary

FEAT-003 is docs + deterministic validation only. The design maps hardware interfaces while preserving a stock-ArduRover-first control path.

## Control Stack

- Pixhawk: primary safety/control interface for RC override, telemetry, rangefinders, and relay/servo spray outputs.
- Raspberry Pi: optional companion computer for later logging/UI/network features; not required for emergency stop or core spray-off safety.
- Pump/valves: controlled only through external MOSFET/relay drivers with flyback protection.
- E-stop: hardwired to actuator/motor power, independent of Pixhawk/RPi software.

## Data / Contract Files

- `hardware/bom-pinout.v0.json`: machine-readable BOM and pinout contract.
- `docs/hardware-bom.md`: human-readable purchasing/planning BOM.
- `docs/pixhawk-rpi-pump-valve-pinout.md`: wiring and safety rules.
- `scripts/validate-hardware-pinout.py`: deterministic validation.

## Safety Rules

- Never power pump or valves directly from Pixhawk pins.
- Prefer normally-closed valves.
- Faults force pump and valves off.
- RC/manual override remains available without Raspberry Pi.
- E-stop cuts motor and spray actuator power independently of software.
