# Architecture Memory

This repository is intended for an automated AGV sprayer and fertigation system.

## System Invariants

- Baseline automated tests must not require live hardware.
- Hardware actions must be isolated behind explicit control boundaries.
- Safety, deterministic behavior, and repeatable validation take priority over convenience.
- Long-lived context belongs in repository files, not chat.
