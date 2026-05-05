# Retire Command

## Purpose

Retire commands revoke a mistaken or obsolete runtime session without deleting audit history.

## Rule

- Retire writes `retire.yaml`.
- Retired sessions are not valid handoff sources.
- Retire requires a reason.
- Retire does not delete run audit.
