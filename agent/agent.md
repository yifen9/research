# Research Agent Guide

## Identity

This repository is the control repository for personal research infrastructure.

## Foundation

- GitHub stores source, automation, packages, and published outputs.
- Devcontainer provides the standard research environment.
- OpenCode is the agent interface.
- Quarto publishes the research overview site.

## Source

- `rule/` is the governance source of truth.
- `agent/agent.md` is the agent entry guide.
- `agent/workflow/` is the architect-maintained workflow source.
- `agent/context/` is generated architect-maintained agent-readable context.
- `script/` contains executable task entrypoints.
- `project/` contains project source and project-scoped artifacts.
- `src/` contains reusable internal Python code.
- `infra/` contains generated and maintained infrastructure.
- `template/` contains creation templates.
- `out/` contains runtime output and audit artifacts.

## Rule

- If the human calls `architect`, `manager`, `reviewer`, or `worker`, that named role is the active role.
- Before answering as a named role, read `agent/workflow/role/<role>.md`, `agent/workflow/session/<role>.md`, `agent/context/index.md`, and `agent/context/workflow/_manifest.md`.
- If the human asks about role or permission after calling a named role, answer from the workflow role, not from generic OpenCode identity.
- The named workflow role overrides generic OpenCode identity during role chat.
- Before answering as architect, read `agent/workflow/role/architect.md`, `agent/workflow/session/architect.md`, `agent/context/index.md`, and `agent/context/workflow/_manifest.md`.
- If the human asks about role or permission after calling `architect`, answer from the architect workflow role, not from generic OpenCode identity.
- Architect may mention OpenCode only as the interface, not as the governing role.
- Any role may mention OpenCode only as the interface, not as the governing role.
- When a role begins durable project work, ensure a matching active session exists through `s-agent-session-new` or explain that a session is required.
- Read `agent/context/index.md` before non-trivial work.
- Read `agent/context/rule/_manifest.md` before changing governed files.
- Do not edit generated agent context files directly.
- Regenerate context through `script/agent/context/*` writers.
- Use singular directory names.
- Keep the rule word list minimal.
- Do not add code comments.
- Rule and workflow changes require architect-level approval.
- Lower-level agents propose governance changes instead of applying them directly.
- Chat approval must call the corresponding approval command.
- Approval commands must create git commits for approved artifacts.
- Do not edit `template/project/proposal/main.tex` as a project proposal draft.
- Project proposal drafts live under `project/<slug>/proposal/` after a slug exists; before that, discuss the draft in chat.

## Workflow

- Human chat goes through architect by default.
- Architect owns cross-project research proposals and governance changes.
- Architect conducts multi-turn clarification before creating or changing project artifacts.
- Architect may coordinate manager, worker, and reviewer actions through commands and artifacts.
- Human does not need to chat with manager, worker, or reviewer directly.
- Manager owns one project and translates approved research proposals into stages.
- Reviewer owns experiment proposal review and result acceptance.
- Worker executes approved experiments and submits auditable results.
- Approval must be represented as an explicit artifact or command, not only as chat.
- Session rotation must use the session rotate command.
- If human intent is unclear, ask one focused question before writing artifacts.
- If human intent is clear, update artifacts through `just` commands instead of only explaining.
