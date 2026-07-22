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
- ArduRover SITL is installed, built, and start-proven locally.
- Full mission-level simulation evidence for row-entry, in-row spray toggles, row-exit, and fault-stop is still not captured.
- Exact row dimensions, drive layout, pump, valves, nozzles, liquid-level sensor, pressure sensor, and selected Pixhawk/firmware version still need owner confirmation.

## Repair / Next Steps

1. Add route and spray contract documents/examples.
2. Add deterministic validation script for route segment spray modes and safety fault behavior.
3. Add a mission-level SITL runner or lighter harness for row-entry, in-row spray toggles, row-exit, and fault-stop.
4. Capture successful mission-level simulation output here.
5. Change this file to `STATUS: PASS` only after mission evidence exists and `bash scripts/check-gate.sh` succeeds.
