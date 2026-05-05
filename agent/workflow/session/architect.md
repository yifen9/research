# Architect Session

## Initial Context

- `agent/agent.md`
- `agent/workflow/role/architect.md`
- `agent/workflow/role/control.md`
- `agent/workflow/session/architect.md`
- `agent/workflow/lifecycle.md`
- `agent/workflow/artifact.md`
- `agent/workflow/command.md`
- `config/agent.yaml`
- `out/agent/memory/architect.md` when present.
- `out/agent/handoff/architect.md` when present.

## Rotate Trigger

- Proposal approved.
- Topic changes.
- Governance source changes.
- Message limit reached.
- Session inactive.

## Rule

- Architect chat starts by loading the initial context list.
- If no active architect session is known, create one before durable project work.
- Architect session writes memory before close.
- Architect close updates role memory for the next architect session.
- Architect writes handoff before close when open work remains.
- Architect uses rotate command for planned session transfer.
- Architect uses retire command for mistaken sessions.
- Architect may maintain workflow and backend manifest source.
