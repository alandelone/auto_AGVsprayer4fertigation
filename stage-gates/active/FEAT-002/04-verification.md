# 04 Verification

STATUS: FAIL

FEAT-002 is advanced from discovery into technical design and execution planning, but it is not passable yet because deterministic contract validation and ArduRover simulation evidence do not exist.

## Commands Run

```bash
python scripts/validate-contracts.py
```

Output:

```text
Validated route/spray/safety contracts: routes/examples/cucumber-row-route.example.json
```

```bash
bash init.sh && bash scripts/check-gate.sh; code=$?; echo CHECK_GATE_EXIT=$code; exit 0
```

Output:

```text
Initializing auto_AGVsprayer4fertigation workspace...
No build or test toolchain is configured yet.
Add setup commands here when source code is introduced.
FAIL: verification gate status must be PASS
CHECK_GATE_EXIT=1
```

```bash
command -v sim_vehicle.py || command -v ardupilot || python - <<'PY'
import shutil
for name in ['sim_vehicle.py','ardurover','mavproxy.py']:
    print(name, shutil.which(name))
PY
```

Output:

```text
sim_vehicle.py None
ardurover None
mavproxy.py None
```

## Design Evidence Added

- `stage-gates/active/FEAT-002/02-tech-design.md` now defines:
  - Pixhawk + ArduRover Phase 1 boundary.
  - RTK waypoint + ultrasonic row-following architecture.
  - Route-segment spray mode contract: `OFF`, `LEFT`, `RIGHT`, `BOTH`.
  - Spray actuator output mapping concept.
  - Safety interlocks for obstacle, low liquid, pressure abnormal, RC override, E-stop, low battery, and lost link.
  - SITL-first test strategy.
- `stage-gates/active/FEAT-002/03-execution.md` now defines:
  - Ordered implementation tasks.
  - Expected files.
  - Validation commands.
  - FEAT-002 definition of done.
- `routes/examples/cucumber-row-route.example.json` now provides a sanitized deterministic route fixture.
- `docs/route-contract.md`, `docs/spray-output-contract.md`, `docs/safety-contract.md`, and `docs/operator-checklist.md` now define route, actuator, safety, and operator behavior.
- `scripts/validate-contracts.py` validates route/spray/safety contracts without hardware.
- `simulation/README.md` records the SITL plan and the current local missing-command blocker.

## External Documentation Checked

- ArduPilot Rover object avoidance/rangefinder docs indicate rangefinders/proximity sensors can be used for obstacle handling, and forward rangefinder is the minimum for obstacle avoidance.
- ArduPilot relay docs indicate relay outputs are GPIO-level control signals with limited current, so pump/valves require external relay/MOSFET/driver hardware.
- ArduPilot mission command docs include relay/servo mission commands suitable for waypoint/segment spray toggling.

## Current Blockers

- No deterministic route/spray/safety validation script exists yet.
- No simulator setup has been selected/proven in this repository yet.
- No ArduPilot SITL run or equivalent simulation evidence exists yet.
- Exact row dimensions, drive layout, pump, valves, nozzles, liquid-level sensor, pressure sensor, and selected Pixhawk/firmware version still need owner confirmation.

## Repair / Next Steps

1. Add route and spray contract documents/examples.
2. Add deterministic validation script for route segment spray modes and safety fault behavior.
3. Add simulation README and attempt ArduRover SITL setup.
4. Capture successful validation/simulation output here.
5. Change this file to `STATUS: PASS` only after evidence exists and `bash scripts/check-gate.sh` succeeds.
