# Claim

## Purpose

Claim artifacts prevent multiple workers from writing the same experiment at the same time.

## File

- `project/<slug>/experiment/<experiment>/claim.yaml`

## Field

- id
- project
- experiment
- kind
- state
- role
- session
- run
- branch
- base
- target
- created
- updated

## State

- claimed
- released

## Rule

- A claimed experiment cannot be claimed by another active worker.
- Claim records role, session, run, and branch.
- Release requires the same role or a higher role.
- Retired sessions are not valid claim owners.
