# Manager Session

## Initial Context

- `agent/agent.md`
- `agent/workflow/role/manager.md`
- `agent/workflow/role/control.md`
- `agent/workflow/session/manager.md`
- `agent/workflow/lifecycle.md`
- `agent/workflow/artifact.md`
- `agent/workflow/command.md`
- `out/agent/memory/manager.md` when present.
- `out/agent/handoff/manager.md` when present.

## Rotate Trigger

- Stage approved.
- Project scope changes.
- Message limit reached.
- Session inactive.

## Rule

- Manager session loads project memory before durable planning.
- Manager session writes memory before close.
- Manager writes handoff before close when open work remains.
- Manager uses rotate command for planned session transfer.
- Manager uses retire command for mistaken sessions.
