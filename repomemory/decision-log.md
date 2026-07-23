# Decision Log

## 2026-07-23: Embed Execution Discipline in AGENTS.md

Decision: Add subagent isolation, code review gates, execution handoff, and verification evidence standard directly to `AGENTS.md` as enforceable No-Go rules.

Reason: FEAT-001–005 audit revealed that the Ubuntu cron agent had no access to IDE-local skills. Process requirements that only exist in local skill files are invisible to remote/autonomous agents. Only `AGENTS.md` and `rules/` are portable.

## 2026-07-22: Merge Mission State into Feature List

Decision: remove `mission_status.json` and use `feature-list.json` as the single source of truth with `active_feature`.

Reason: reduces duplicated state and prevents conflicting task pointers.

## 2026-07-21: Use Filesystem-Based Progressive Disclosure

Decision: split context into hot, warm, and cold repository files.

Reason: protects prompt cache, reduces attention pollution, and enables reliable session handoff.
