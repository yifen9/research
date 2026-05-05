# Worker Session

## Initial Context

- `agent/agent.md`
- `agent/workflow/role/worker.md`
- `agent/workflow/role/control.md`
- `agent/workflow/session/worker.md`
- `agent/workflow/lifecycle.md`
- `agent/workflow/artifact.md`
- `agent/workflow/command.md`
- `out/agent/memory/worker.md` when present.
- `out/agent/handoff/worker.md` when present.

## Rotate Trigger

- Result submitted.
- Experiment scope changes.
- Message limit reached.
- Session inactive.

## Rule

- Worker session loads experiment proposal and active claim before execution.
- Worker session writes memory before close.
- Worker writes handoff before close when open work remains.
- Worker uses rotate command for planned session transfer.
- Worker uses retire command for mistaken sessions.
