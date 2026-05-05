# Approve Command

## Purpose

Approval commands turn chat approval into durable decision artifacts.

## Rule

- Human approval may be chat-triggered.
- Approval must call a command and write `decision.yaml`.
- Project proposal approval writes `project/<slug>/proposal/decision.yaml`.
- Approval must create a git commit for the approved artifact.
- Approval commit messages must state the approved artifact and why it is being activated.
- Approval commits should happen on scoped branches rather than the main line.
- Project proposal approval uses `project/<slug>/approve` as the scoped branch.
- Higher roles merge or rebase scoped branches after review.
