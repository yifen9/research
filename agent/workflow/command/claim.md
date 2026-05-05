# Claim Command

## Purpose

Claim commands reserve an experiment for one worker session.

## Rule

- Claim must write `claim.yaml`.
- Claim must fail if the experiment is already claimed.
- Claim must record role, session, run, and scoped branch.
