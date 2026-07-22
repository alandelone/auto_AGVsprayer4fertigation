# 04 Verification

STATUS: PASS

FEAT-003 provides hardware BOM and Pixhawk/Raspberry Pi/pump/valve pinout references without requiring ArduRover firmware changes.

## Commands Run

```bash
python scripts/validate-hardware-pinout.py
```

Expected output:

```text
Validated hardware BOM/pinout contract: hardware/bom-pinout.v0.json
```

```bash
bash init.sh && bash scripts/check-gate.sh
```

Expected output includes:

```text
Gate check passed
Validated route/spray/safety contracts: routes/examples/cucumber-row-route.example.json
Mission contract simulation PASS: routes/examples/cucumber-row-route.example.json
Validated hardware BOM/pinout contract: hardware/bom-pinout.v0.json
```

## Evidence

- `hardware/bom-pinout.v0.json` contains the deterministic BOM/pinout contract.
- `docs/hardware-bom.md` gives the prototype purchase/planning BOM.
- `docs/pixhawk-rpi-pump-valve-pinout.md` gives signal mapping, voltage/isolation rules, failsafe output policy, and firmware boundary.
- `scripts/validate-hardware-pinout.py` protects required BOM categories and pinout signals.

## Remaining Later Work

- Select exact pump/nozzle/valve ratings after bench flow tests.
- Choose exact sensor voltage/interface variants before wiring.
- Create a separate feature for MAVLink/Mission Planner export only if needed later.
- Create a separate firmware feature only if stock ArduRover outputs and parameters cannot satisfy prototype needs.
