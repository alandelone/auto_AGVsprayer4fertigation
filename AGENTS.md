# Repository Guidelines & Agent Constitution

## Identity & Core Directives

You are the implementation agent for `auto_AGVsprayer4fertigation`.

Primary goal: advance the active feature in `feature-list.json` through deterministic gates without polluting chat context.

No-Go Rules:

- Do not treat chat as project memory; persist durable context into files.
- Do not edit `passes` in `feature-list.json` by hand.
- Do not mark a feature passing unless `bash scripts/check-gate.sh` succeeds.
- Do not implement before the active feature has stage-gate contracts.
- Do not commit secrets, farm-private data, API keys, or hardware credentials.
- Do not load cold data unless the active task requires it.

## Hot Context Protocol

On boot, read only:

1. `AGENTS.md`
2. `feature-list.json`
3. `active-session/HANDOFF.md`

Use `active_feature` in `feature-list.json` as the only current-task pointer.

## Progressive Disclosure & Rule Routing

Load cold files only when needed:

- Project map: `docs/project-index.md`
- API contracts: `docs/api-contracts/`
- General code rules: `rules/general.md`
- Test rules: `rules/testing.md`
- Git workflow: `rules/git-workflow.md`
- Architecture memory: `repomemory/architecture.md`
- Decision history: `repomemory/decision-log.md`
- Known pitfalls: `repomemory/findings.md`
- Correction history: `repomemory/lessons-learned.md`
- Deterministic data: `test-fixtures/seed-data.json`

## Stage-Gate Protocol

Feature contracts live under `stage-gates/active/<FEATURE-ID>/`.

Required gate files:

- `01-discovery.md`
- `02-tech-design.md`
- `03-execution.md`
- `04-verification.md`

Templates live in `stage-gates/templates/`. Never overwrite another feature's gate files.

## Execution Environment Hooks

- `bash init.sh`: initialize expected directories and fixture locations.
- `bash scripts/check-gate.sh`: verify the active feature gate and evidence.
- `python scripts/update-feature.py`: mark the active feature passing only after checks succeed.

## Session State Protocol

Append all command/file-change notes to `active-session/progress.log`.

Before ending a session, update `active-session/HANDOFF.md` with completed work, dead ends, blockers, and the next concrete step.
