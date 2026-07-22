# FEAT-004 Technical Design

## Design

Use a low-pressure two-zone bench sprayer: a 12 V diaphragm pump feeds left/right normally-closed solenoid valves, each driving one 110° flat-fan nozzle. Pixhawk relay/servo outputs only control isolated driver inputs. Physical e-stop and low-liquid/pressure interlocks cut actuator power independently of Raspberry Pi software.

## Selected Rating Contract

Machine-readable contract: `hardware/bench-test-ratings.v0.json`.

Human reference: `docs/bench-test-hardware-selection.md`.

## Verification Strategy

`validate-bench-ratings.py` checks minimum pump pressure/flow, nozzle flow math, pressure limits, valve fail-closed behavior, driver channels, fuse sizing, and source/evidence fields.
