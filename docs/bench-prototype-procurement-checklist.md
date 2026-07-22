# Bench Prototype Procurement Checklist

## Scope

FEAT-006 converts the bench ratings into a purchase checklist. It does not perform checkout, store supplier credentials, or finalize farm-specific mounting dimensions.

## Buy List

- **Pump**: 1x 12 V DC diaphragm sprayer pump, ≥5 L/min, ≥60 PSI, ≤8 A expected current, pressure switch preferred.
- **Nozzles**: 2x 11002-class 110° flat-fan tips, ~0.20 GPM at 40 PSI; buy compatible caps/holders. Optional spares: 110015 and 11003.
- **Valves**: 2x 12 V normally-closed solenoid valves, ≥100 PSI, ≥4 mm orifice, water compatible.
- **Driver board**: 1x opto-isolated MOSFET/relay board, ≥3 channels, ≥10 A pump channel, inductive-load/flyback protection.
- **Pressure sensing**: 1x 0–1.2 MPa pressure transducer or high/low switch; safe ADC/interface for Pixhawk/RPi.
- **Low liquid**: 1x tank float switch or non-contact level sensor wired as pump-off interlock.
- **Safety/power**: physical e-stop, 10 A pump fuse, 3 A valve fuse, 12 V distribution, separated logic supply, wire sized for pump current.
- **Fluid path**: suction filter, 0–100 PSI pressure gauge, tubing, clamps, check valves/anti-drip plan, tee fittings, tank fittings, nozzle holders.
- **Controller stack**: Pixhawk-compatible ArduRover controller, RC override path, telemetry radio pair, GPS/compass, optional Raspberry Pi buck supply.

## Purchase Rules

- Every required item must have pressure/current/voltage/interface ratings visible before purchase.
- Reject normally-open spray valves; use normally-closed only.
- Reject any plan that powers pump or valves directly from Pixhawk pins.
- Reject software-only emergency stop; e-stop must cut actuator power.
- Do not buy fertilizer/chemical for testing until water-only bench tests pass.
- Do not commit real supplier accounts, farm coordinates, payment data, or private shipping details.

## Receiving Inspection

1. Photograph labels/spec plates for pump, valves, pressure sensor, driver board, and power modules.
2. Confirm valve flow direction and normally-closed behavior before plumbing.
3. Confirm fuse ratings before connecting actuator rail.
4. Confirm hose/fitting sizes match before cutting tubing.
5. Confirm pressure gauge/transducer range covers 0–70 PSI bench tests.
6. Record inspection in `templates/procurement-inspection-log.template.json`.
