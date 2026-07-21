# Decision Log

## 2026-07-22: Merge Mission State into Feature List

Decision: remove `mission_status.json` and use `feature-list.json` as the single source of truth with `active_feature`.

Reason: reduces duplicated state and prevents conflicting task pointers.

## 2026-07-21: Use Filesystem-Based Progressive Disclosure

Decision: split context into hot, warm, and cold repository files.

Reason: protects prompt cache, reduces attention pollution, and enables reliable session handoff.
