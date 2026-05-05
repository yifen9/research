# Question

## Purpose

Question artifacts record upward questions from a lower role to a higher role.

## File

- `project/<slug>/question/<question>/meta.yaml`

## State

- open
- answered

## Field

- id
- project
- kind
- state
- role
- target_role
- target
- question
- run
- branch
- base
- created
- updated

## Rule

- Lower roles ask upward through question artifacts.
- Higher roles answer through the answer command.
- Chat alone is not durable role coordination.
