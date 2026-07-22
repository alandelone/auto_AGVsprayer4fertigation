# FEAT-006 Technical Design

## Design

Add a machine-readable procurement checklist plus a human buy list and receiving inspection log template. Required procurement items must include qty, must-have specs, reject criteria, and safety/private-data constraints.

## Files

- `hardware/procurement-checklist.v0.json`
- `docs/bench-prototype-procurement-checklist.md`
- `templates/procurement-inspection-log.template.json`
- `scripts/validate-procurement-checklist.py`

## Verification Strategy

Validator checks required item coverage, IDs, must-have specs, reject criteria, safety constraints, and inspection log alignment.
