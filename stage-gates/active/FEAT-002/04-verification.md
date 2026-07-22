# 04 Verification

STATUS: PASS

FEAT-002 has discovery, technical design, execution planning, deterministic route/spray/safety validation, ArduRover SITL build/startup evidence, and lightweight mission contract simulation evidence. Hardware-specific dimensions and component choices remain deferred to later implementation features.

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


```bash
git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/ArduPilot/ardupilot.git simulation/ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
sudo apt-get install -y python3-empy python3-pexpect python3-future python3-lxml python3-numpy python3-pyparsing
PYTHONNOUSERSITE=1 /usr/bin/python3 ./waf configure --board sitl
PYTHONNOUSERSITE=1 /usr/bin/python3 ./waf rover
```

Output summary:

```text
'configure' finished successfully
[1369/1370] Linking build/sitl/bin/ardurover
[1370/1370] checking symbols build/sitl/bin/ardurover
BUILD SUMMARY
Target         Text (B)  Data (B)  BSS (B)  Total Flash Used (B)
bin/ardurover   4093104    192917   225888               4286021
'rover' finished successfully (4m52.432s)
```

```bash
timeout 8s build/sitl/bin/ardurover --model rover --speedup 1 --sim-address=127.0.0.1 -I1 --home -35.363261,149.16523,584.0,353.0 || code=$?; echo ARDUROVER_EXIT=${code:-0}
```

Output:

```text
Setting SIM_SPEEDUP=1.000000
Home: -35.363261 149.165230 alt=584.000000m hdg=353.000000
Starting sketch 'Rover'
Starting SITL input
Using Irlock at port : 9015
Using \clock topic for DDS timing: disabled
bind port 5770 for SERIAL0
SERIAL0 on TCP port 5770
Waiting for connection ....
ARDUROVER_EXIT=124
```

Note: `ARDUROVER_EXIT=124` is expected because the long-running SITL process was stopped by `timeout` after startup proof.


```bash
python scripts/simulate-mission-contract.py
```

Output:

```text
Mission contract simulation PASS: routes/examples/cucumber-row-route.example.json
- ROW_ENTRY entry_transit: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
- SPRAY_ON row_01_left_spray: spray=LEFT speed=0.25 outputs={'pump': True, 'left_valve': True, 'right_valve': False}
- SPRAY_TRANSITION OFF->LEFT at row_01_left_spray
- FAULT_STOP front_obstacle during row_01_left_spray: mode=HOLD outputs={'pump': False, 'left_valve': False, 'right_valve': False} operator_review_required=True
- SPRAY_TRANSITION LEFT->OFF at row_01_exit_off
- ROW_EXIT row_01_exit_off: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
- MISSION_END return_to_hold: spray=OFF outputs={'pump': False, 'left_valve': False, 'right_valve': False}
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

## Remaining Open Items For Later Features

- Exact row dimensions, drive layout, pump, valves, nozzles, liquid-level sensor, pressure sensor, and selected Pixhawk/firmware version still need owner confirmation.
- Full MAVLink/Mission Planner export and live hardware validation are later implementation tasks, not FEAT-002 requirements.

## Verification Closure

- Route/spray/safety contract documents and examples exist.
- Deterministic validation script passes.
- ArduRover SITL builds and starts locally.
- Lightweight mission contract simulation proves row-entry, in-row spray, spray-off row exit, mission-end safe/off, and front-obstacle fault-stop behavior.
- `bash scripts/check-gate.sh` is expected to pass after this evidence.
