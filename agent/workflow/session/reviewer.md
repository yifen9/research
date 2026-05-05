# Reviewer Session

## Initial Context

- `agent/agent.md`
- `agent/workflow/role/reviewer.md`
- `agent/workflow/role/control.md`
- `agent/workflow/session/reviewer.md`
- `agent/workflow/lifecycle.md`
- `agent/workflow/artifact.md`
- `agent/workflow/command.md`
- `out/agent/memory/reviewer.md` when present.
- `out/agent/handoff/reviewer.md` when present.

## Rotate Trigger

- Result accepted or rejected.
- Stage scope changes.
- Message limit reached.
- Session inactive.

## Rule

- Reviewer session loads experiment proposal and run audit before deciding.
- Reviewer session writes memory before close.
- Reviewer writes handoff before close when open work remains.
- Reviewer uses rotate command for planned session transfer.
- Reviewer uses retire command for mistaken sessions.
