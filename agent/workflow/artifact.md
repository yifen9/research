# Artifact

## Proposal

- `project/<slug>/proposal/meta.yaml`
- `project/<slug>/proposal/main.tex`
- `project/<slug>/proposal/decision.yaml`
- `project/<slug>/stage/<stage>/meta.yaml`
- `project/<slug>/experiment/<experiment>/meta.yaml`

### Rule

- A proposal without `decision.yaml` is not approved.
- Draft proposals do not require PDF output.
- Human approval may be chat-triggered but must call an approval command.
- Project proposals live under the project slug.

## Decision

- `project/<slug>/proposal/decision.yaml`
- `project/<slug>/stage/<stage>/decision.yaml`
- `project/<slug>/experiment/<experiment>/decision.yaml`

### Rule

- Decision artifacts represent durable approval or rejection.
- Decision artifacts must reference the artifact they decide.

## Result

- `project/<slug>/experiment/<experiment>/result/<id>.yaml`
- `project/<slug>/repo/<repo>/out/run/<run>/`

### Rule

- Result artifacts must reference the run audit directory.
- Result artifacts are submitted by worker and reviewed by reviewer.

## Review

- `project/<slug>/experiment/<experiment>/review/<id>.yaml`

### Rule

- Review artifacts must reference the result they review.
- Review artifacts must record reviewer role and decision.

## Question

- `project/<slug>/question/<id>.yaml`

### Rule

- Question artifacts target a specific role or specific artifact.
- Question artifacts are answered by the answer command.

## Handoff

- `out/agent/handoff/<role>.md`

### Rule

- Handoff artifacts are written before session close when open work remains.
- Handoff artifacts are read by the next session of the same role.

## Memory

- `out/agent/memory/<role>.md`

### Rule

- Memory artifacts are role-scoped and survive across sessions.
- Memory artifacts are written before session close.

## Meta

- `project/<slug>/proposal/meta.yaml`
- `project/<slug>/stage/<stage>/meta.yaml`
- `project/<slug>/experiment/<experiment>/meta.yaml`

### Rule

- Meta artifacts record kind, slug, state, and title.
- Meta artifacts are updated by command-driven state transitions.

## Claim

- `project/<slug>/experiment/<experiment>/claim.yaml`

### Rule

- One experiment may have only one active claim.
- Claim artifacts are released before another role may claim the experiment.
