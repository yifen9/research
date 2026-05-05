# Architect Session

## Initial Context

- `agent/agent.md`
- `agent/context/index.md`
- `agent/context/rule/_manifest.md`
- `agent/context/project/overview.md`
- `agent/context/profile/user/research.md`
- `agent/context/profile/user/projects.md`
- `agent/context/run/latest.md`
- `agent/workflow/role/architect.md`
- `agent/workflow/session/architect.md`
- `out/agent/memory/architect.md`
- `out/agent/handoff/architect.md`

## Rotate Trigger

- Proposal approved.
- Topic changes.
- Governance source changes.
- Message limit reached.
- Session inactive.

## Rule

- Architect session writes memory before close.
- Architect close updates role memory for the next architect session.
- Architect writes handoff before close when open work remains.
- Architect uses rotate command for planned session transfer.
- Architect uses retire command for mistaken sessions.
- Architect can maintain workflow and context source.
