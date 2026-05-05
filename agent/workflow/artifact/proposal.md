# Proposal

## Purpose

Proposal artifacts define intended project, stage, or experiment work before execution.

## File

- `project/<slug>/proposal/meta.yaml`
- `project/<slug>/proposal/main.tex`
- `project/<slug>/proposal/decision.yaml`

## State

- draft
- proposed
- approved
- active
- complete
- accepted
- rejected
- blocked
- amend

## Rule

- A proposal without `decision.yaml` is not approved.
- Draft proposals do not require PDF output.
- Human approval may be chat-triggered but must call an approval command.
- Project proposals live under the project slug.
