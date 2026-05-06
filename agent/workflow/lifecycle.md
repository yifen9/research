# Lifecycle

## Session

### State

- active
- closed
- retired

### Rule

- Session artifacts live under `out/agent/session/<role>/<id>/`.
- Session creation connects to the configured vector backend.
- Active session writes memory before close.
- Active session writes handoff before close when open work remains.
- Session rotation must use the session rotate command.
- Mistaken sessions are removed via the retire command.

## Governance

### State

- proposed
- approved
- applied

### Rule

- Rule, workflow, backend manifest, and template changes require architect-level approval.
- Approval commits should happen on scoped branches rather than the main line.
- Approval must create a git commit for the approved artifact.
