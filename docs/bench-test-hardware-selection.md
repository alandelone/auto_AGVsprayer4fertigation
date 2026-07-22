# Bench Test Hardware Selection

## Scope

FEAT-004 chooses concrete ratings for a bench/prototype spray system. It does not finalize supplier purchase, vehicle dimensions, firmware, or real farm deployment.

## Recommended Bench Ratings

- Pump: 12 V DC diaphragm sprayer pump, at least 5 L/min, at least 60 PSI, pressure-switch type, fused at 10 A.
- Nozzles: two 110° flat-fan agricultural spray tips, TeeJet XR/TP11002-class, about 0.20 GPM each at 40 PSI.
- Valves: two 12 V normally-closed solenoid valves, at least 100 PSI pressure rating, at least 4 mm orifice, about <=1 A each design current.
- Pressure sensor: 0–1.2 MPa water pressure transducer or equivalent high/low pressure switch. Bench trips: low <15 PSI, high >70 PSI.
- Liquid level: float switch or non-contact tank sensor wired as an interlock; low liquid disables pump/valves and requires manual reset.
- Drivers: opto-isolated MOSFET/relay board, 3 channels minimum, 10 A/channel minimum preferred, flyback protection required.
- Power: 12 V actuator rail, pump 10 A fuse, valve rail 3 A fuse, separated logic power for Pixhawk/Raspberry Pi.

## Sizing Check

- 1 nozzle at 40 PSI: 0.76 L/min.
- 2 nozzles at 40 PSI: 1.51 L/min.
- 5 L/min pump margin vs both nozzles: 3.30x nominal flow.

This is enough for low-speed cucumber row bench testing while avoiding oversized pressure/flow that would increase drift and leakage risk. Final field calibration still requires catch-cup measurement and crop-safe application-rate testing.

## Procurement Notes

- Prefer reputable sprayer parts for nozzle repeatability; generic pumps are acceptable for bench only.
- Buy spare nozzle sizes one step down/up, e.g. 110015 and 11003, if local coverage tests need adjustment.
- Use water-only tests first; no chemical/fertilizer tests until leak, pressure, and e-stop behavior are proven.
- Do not connect pump/valve loads directly to Pixhawk pins.
