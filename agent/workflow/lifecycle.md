# Lifecycle

## Project

### State

- idea
- proposal
- active
- stage
- result
- publish
- archive

### Rule

- Project directories use slug names.
- Project proposals live under `project/<slug>/proposal/`.
- Project activation requires `project/<slug>/proposal/decision.yaml`.

## Stage

### State

- draft
- proposed
- approved
- active
- complete
- accepted
- rejected

### Rule

- Stage is managed by manager.
- Stage artifacts live under `project/<slug>/stage/<stage>/`.
- Active projects may have active stages before result review.
- Stage output is reviewed before project aggregation.

## Experiment

### State

- new
- ready
- running
- result
- review
- accepted
- rejected
- failed
- amend

### Rule

- Experiment execution requires approved experiment proposal.
- Experiment artifacts live under `project/<slug>/experiment/<experiment>/`.
- Worker execution requires an experiment claim.
- One experiment may have only one active claim.
- Worker output requires reviewer decision.

## Session

### State

- active
- closed
- retired

### Rule

- Session artifacts live under `out/agent/session/<role>/<id>/`.
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
