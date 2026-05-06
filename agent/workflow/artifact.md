# Artifact

## Message

- `out/agent/session/<role>/<id>/message.jsonl`

### Rule

- Every recorded message is appended to `message.jsonl`.
- Every recorded message is ingested into the configured vector backend.
- Message text is redacted according to `config/agent.yaml` before durable write.

## Session

- `out/agent/session/<role>/<id>/meta.yaml`
- `out/agent/session/<role>/<id>/message.jsonl`

### Rule

- Session artifacts are created by session commands.
- Session creation connects to the configured vector backend.
- Session heartbeat checks and repairs missing vector entries.

## Handoff

- `out/agent/handoff/<role>.md`
- source template: `config/template/agent/handoff.md`

### Rule

- Handoff artifacts are written before session close when open work remains.
- Handoff artifacts are read by the next session of the same role.
- Handoff artifacts include review, summary, next, risk, and choice sections.

## Memory

- `out/agent/memory/<role>.md`
- source template: `config/template/agent/memory.md`

### Rule

- Memory artifacts are role-scoped and survive across sessions.
- Memory artifacts are written before close.
- Memory artifacts include review, summary, next, risk, and choice sections.

## Backend Config

- `agent/backend/<name>/manifest.yaml`
- `agent/backend/<name>/template/`
- root backend config rendered from the active template.

### Rule

- Root backend config is generated and ignored by git.
- Backend check verifies generated root config matches the active backend template.

## Decision

- Approval command output.
- Approval commit.

### Rule

- Durable governance and backend changes require explicit approval.
- Approval must create a commit for the approved artifact.
