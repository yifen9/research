# Research Agent Guide

## Identity

This repository is the control repository for personal research infrastructure.

## Source

- GitHub stores source, automation, packages, and published outputs.
- Devcontainer provides the standard research environment.
- `config/rule/` is the governance source of truth.
- `config/template/` is reusable template source.
- `config/agent.yaml` selects the active backend and vector backend.
- `agent/agent.md` is the agent entry guide.
- `agent/workflow/` is the minimal architect workflow source.
- `agent/backend/` is backend manifest and template source.
- `doc/` contains the Quarto site source.
- `script/` contains executable task entrypoints.
- `src/` contains reusable internal Python code.
- `out/` contains runtime audit artifacts and may be cleared.

## Priority

- P0: active backend only, architect role only, vector backend required, session command required, every message written to `message.jsonl` and vector backend, memory written before close.
- P1: singular directory names, generated backend root config ignored by git, backend config rendered from the active backend template, workflow and backend changes require architect approval.
- P2: strict naming vocabulary, Python/code limits, no code comments unless explicitly approved, no silent fallback for required infrastructure.

## Rule

- Human chat goes through architect by default.
- Dialogue with the human is Chinese by default; durable artifacts are English by default.
- Offer bounded choices to the human whenever possible.
- The active backend is the only backend the human chats through.
- Components must remain replaceable through explicit config and command contracts.
- Backend-specific configuration files are rendered from `agent/backend/<name>/template/` to the repository root.
- Backend-specific configuration files at the repository root are not committed.
- Before durable workflow work, read `agent/workflow/role/architect.md`, `agent/workflow/session/architect.md`, `config/rule/`, and `config/agent.yaml`.
- Architect workflow identity overrides the backend identity during role chat.
- Rule, workflow, and backend manifest changes require architect-level approval.
- Approval commands must create git commits for approved artifacts.
