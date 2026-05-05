# Approve Command

## Purpose

Approval commands turn chat approval into durable decision artifacts.

## Rule

- Human approval may be chat-triggered.
- Approval must call a command and write `decision.yaml`.
- Project proposal approval writes `project/<slug>/proposal/decision.yaml`.
