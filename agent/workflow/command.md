# Command

## Approve

- Approval turns chat approval into durable decision artifacts.
- Approval must call a command and write `decision.yaml`.
- Project proposal approval writes `project/<slug>/proposal/decision.yaml`.
- Approval must create a git commit for the approved artifact.
- Approval commit messages must state the approved artifact and why it is being activated.
- Approval commits should happen on scoped branches rather than the main line.

## Reject

- Rejection turns chat rejection into durable decision artifacts.
- Rejection writes `decision.yaml` with rejected state and reason.
- Rejection must create a git commit for the rejected artifact.

## Ask

- Ask raises a question artifact targeting a higher role or specific artifact.
- Ask records the asking role and the target.

## Answer

- Answer resolves a question artifact.
- Answer records the answering role and the resolution text.

## Claim

- Claim records that a worker has taken an experiment.
- One experiment may have only one active claim.

## Release

- Release ends an active claim before completion.
- Release records the releasing role and reason.

## Submit

- Submit writes a result artifact for an experiment.
- Submit references the run audit directory.

## Scan

- Scan inspects project artifacts and reports state inconsistencies.

## Close

- Close ends an active session.
- Close writes memory before terminating.

## Rotate

- Rotate transfers an active session to a new session of the same role.
- Rotate writes memory and handoff before terminating the old session.

## Retire

- Retire removes a mistaken session.
- Retire records the reason for retirement.
