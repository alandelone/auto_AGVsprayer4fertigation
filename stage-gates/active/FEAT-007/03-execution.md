# FEAT-007 Execution Plan

## Components

1. **Mission source contract**
   - Create `missions/cucumber-row-mission.v0.json` with deterministic synthetic route points, row labels, speed targets, and spray states.

2. **Exporter**
   - Create `scripts/export-mission-files.py` to generate `.plan` and `.waypoints` artifacts from the source contract and FEAT-006 actuator mapping.

3. **Validator and verification evidence**
   - Create `scripts/validate-mission-exports.py` and wire it into `scripts/check-gate.sh`.
   - Run exporter, validator, and repo gate.
   - Paste actual command/output evidence into `04-verification.md` and set `STATUS: PASS` only after success.

## Review Gates

After each component, append a `REVIEW FEAT-007 <component>: PASS|FAIL <summary>` line to `active-session/progress.log` before continuing.

## Notes

This is a multi-component feature. In an interactive session, use subagent-driven or parallel-session execution as required by `AGENTS.md`. In scheduled heartbeat mode, only take small bounded steps and leave the next concrete component in `active-session/HANDOFF.md`.
