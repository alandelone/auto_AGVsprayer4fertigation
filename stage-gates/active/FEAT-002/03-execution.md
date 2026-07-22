# 03 Execution

## Goal

Convert the FEAT-002 discovery and technical design into an implementation contract that can be executed deterministically without live farm hardware by default.

## Execution Status

STATUS: IMPLEMENTED FOR CONTRACT VALIDATION

FEAT-002 has deterministic contract validation, a lightweight mission contract simulation, and ArduRover SITL build/startup evidence. Hardware dimensions and component choices remain open for the later implementation phase.

## Ordered Tasks

### Task 1: Add Route/Spray Contract Files

Expected files:

- `routes/examples/cucumber-row-route.example.json`
- `docs/route-contract.md`

Work:

- Define route segment schema with `id`, `type`, `spray`, `target_speed_mps`, and waypoint references.
- Require spray mode enum: `OFF`, `LEFT`, `RIGHT`, `BOTH`.
- Require explicit `OFF` on transit, turn, abort, RTL, and mission-end segments.

Done when:

- Example route has row-entry, in-row spray, transit-only, row-exit, and return segments.
- Documentation explains how this maps to Mission Planner waypoint/DO commands.

### Task 2: Add Spray Output Mapping

Expected files:

- `docs/spray-output-contract.md`
- Optional later source file: `src/spray_outputs.*` or equivalent once language/toolchain is selected.

Work:

- Define mapping from spray mode to pump/left-valve/right-valve outputs.
- Record default-safe state: pump off, valves off.
- Document relay/servo/PWM options and external driver requirement.

Done when:

- `OFF`, `LEFT`, `RIGHT`, `BOTH` have unambiguous output states.
- Safety faults always map to `OFF`.

### Task 3: Add Safety/Fault Contract

Expected files:

- `docs/safety-contract.md`
- `docs/operator-checklist.md`

Work:

- Define fault inputs: front obstacle, invalid side sensor, low liquid, low pressure, high pressure, low battery, RC loss, telemetry loss, E-stop.
- Define required behavior per fault.
- Add pre-run operator checklist.

Done when:

- Every mandatory safety requirement from discovery has a concrete behavior.
- Manual override and physical E-stop are explicitly described.

### Task 4: Select Simulation Path

Expected files:

- `simulation/README.md`
- `simulation/README.md` with proven ArduRover SITL setup and startup evidence.
- `scripts/simulate-mission-contract.py` for deterministic route/spray/fault behavior evidence.

Work:

- Use ArduPilot SITL as first candidate.
- Define minimal representative mission: row entry, in-row travel, spray-on segment, spray-off segment, row exit, return/hold.
- Define how to inject or simulate obstacle/fault behavior.

Done when:

- Repository contains reproducible commands for running the simulation or a documented blocker explaining why SITL cannot run in this environment.

### Task 5: Add Deterministic Validation Script

Expected files:

- `scripts/validate-contracts.py`
- `test-fixtures/seed-data.json` update if needed.

Work:

- Validate route examples contain explicit spray modes.
- Validate no transit/turn/abort/RTL/mission-end segment has spray enabled.
- Validate known spray modes map to safe output states.
- Validate required safety faults are listed.

Done when:

- Validation runs locally without hardware.
- `bash scripts/check-gate.sh` invokes or references validation evidence.

### Task 6: Record Verification Evidence

Expected files:

- `stage-gates/active/FEAT-002/04-verification.md`
- `active-session/progress.log`
- `active-session/HANDOFF.md`

Work:

- Record exact commands run and outputs.
- Keep `STATUS: FAIL` until simulation and validation evidence satisfy the feature gate.
- Only after `bash scripts/check-gate.sh` succeeds, run `python scripts/update-feature.py` to update `feature-list.json`.

Done when:

- Verification contains command evidence, known blockers, and next repair steps.

## Files Expected To Change First

- `stage-gates/active/FEAT-002/02-tech-design.md`
- `stage-gates/active/FEAT-002/03-execution.md`
- `stage-gates/active/FEAT-002/04-verification.md`
- `active-session/progress.log`
- `active-session/HANDOFF.md`

## Validation Commands

Run after each meaningful change:

```bash
bash init.sh
bash scripts/check-gate.sh
```

Run once deterministic validation exists:

```bash
python scripts/validate-contracts.py
bash scripts/check-gate.sh
```

Run after SITL setup exists:

```bash
# exact SITL command to be added in simulation/README.md after installation path is proven
```

## Commit/Push Contract

- Commit each logical repository change.
- Push every commit to the configured remote when authentication permits.
- Do not hand-edit `feature-list.json` passes.
- Do not commit secrets, farm-private coordinates, or hardware credentials.

## Definition Of Done For FEAT-002

FEAT-002 can be marked passing only when all are true:

- Discovery requirements are captured.
- Technical design is complete enough for implementation.
- Execution contract identifies files, tasks, and validation commands.
- Deterministic route/spray/safety validation exists.
- ArduRover SITL or selected simulator evidence shows representative route and safety behavior.
- `04-verification.md` contains `STATUS: PASS` with real evidence.
- `bash scripts/check-gate.sh` exits successfully.
- `python scripts/update-feature.py` marks FEAT-002 passing.
