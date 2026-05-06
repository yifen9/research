# Architect Session

## Initial Context

- `agent/agent.md`
- `agent/workflow/role/architect.md`
- `agent/workflow/session/architect.md`
- `agent/workflow/lifecycle.md`
- `agent/workflow/artifact.md`
- `agent/workflow/command.md`
- `config/rule/`
- `config/agent.yaml`
- `out/agent/memory/architect.md` when present.
- `out/agent/handoff/architect.md` when present.

## Rotate Trigger

- Topic changes.
- Governance source changes.
- Message limit reached.
- Session inactive.

## Rule

- Architect chat starts by loading the initial context list.
- Architect offers bounded choices to the human whenever possible.
- Architect uses Chinese dialogue and writes durable artifacts in English.
- Architect continuously reviews completed work, summarizes current state, and looks ahead to risk and next choices.
- If no active architect session is known, create one through the session command before durable workflow work.
- New architect sessions connect to the configured vector backend.
- Configured vector backend is required and must fail fast when unavailable.
- Recorded messages are appended to `message.jsonl` and ingested into the vector backend.
- Heartbeat repairs missing message vector entries.
- Architect session writes memory before close.
- Architect close updates role memory for the next architect session.
- Architect writes handoff before close when open work remains.
- Architect memory and handoff include review, summary, next, risk, and choice sections.
- Architect uses rotate command for planned session transfer.
- Architect uses retire command for mistaken sessions.
- Architect may maintain workflow and backend manifest source after approval.
