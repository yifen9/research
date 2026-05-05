# Experiment Lifecycle

## State

- new
- ready
- running
- result
- review
- accepted
- rejected
- failed
- amend

## Rule

- Experiment execution requires approved experiment proposal.
- Experiment artifacts live under `project/<slug>/experiment/<experiment>/`.
- Worker execution requires an experiment claim.
- One experiment may have only one active claim.
- Worker output requires reviewer decision.
