# Research Agent Guide

## Identity

This repository is the control repository for personal research infrastructure.

## Foundation

- GitHub stores source, automation, packages, and published outputs.
- Devcontainer provides the standard research environment.
- Quarto publishes the research overview site.
- The active agent backend is selected by `config/agent.yaml`.

## Source

- `rule/` is the governance source of truth.
- `agent/agent.md` is the agent entry guide.
- `agent/workflow/` is the architect-maintained workflow source.
- `agent/backend/` is the per-backend manifest and template source.
- `agent/context/` is generated agent-readable context.
- `config/` is repository configuration source.
- `script/` contains executable task entrypoints.
- `src/` contains reusable internal Python code.
- `infra/` contains generated and maintained infrastructure.
- `template/` contains creation templates.
- `out/` contains runtime output and audit artifacts.

## Rule

- The active backend is the only backend the human chats through.
- Backend-specific configuration files are rendered from `agent/backend/<name>/template/` to the repository root.
- Backend-specific configuration files at the repository root are not committed.
- If the human calls `architect`, `manager`, `reviewer`, or `worker`, that named role is the active role.
- Before answering as a named role, read `agent/workflow/role/<role>.md` and `agent/workflow/session/<role>.md`.
- The named workflow role overrides the backend identity during role chat.
- Use singular directory names.
- Do not edit generated agent context files directly.
- Regenerate context through `script/agent/context/*` writers.
- Do not add code comments.
- Rule, workflow, and backend manifest changes require architect-level approval.
- Lower-level agents propose governance changes instead of applying them directly.
- Approval commands must create git commits for approved artifacts.

## Workflow

- Human chat goes through architect by default.
- Architect owns cross-project research proposals and governance changes.
- Architect coordinates manager, reviewer, and worker actions through commands and artifacts.
- Manager owns one project and translates approved research proposals into stages.
- Reviewer owns experiment proposal review and result acceptance.
- Worker executes approved experiments and submits auditable results.
- Approval must be represented as an explicit artifact or command, not only as chat.
- Project artifacts live under `project/<slug>/`.
