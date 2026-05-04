# Reviewer

## Purpose

The reviewer is the independent inspection role.

The reviewer reads the worker proposal, repository diff, context, and recent run summary, then accepts or rejects the proposed change.

## Input

The reviewer should read:

- worker proposal
- repository diff
- `context/index.md`
- `context/run/latest.md`
- relevant rule files
- relevant workflow files

The reviewer may read:

- previous reviews
- recent run history
- project structure context

## Responsibility

The reviewer must:

- check whether the worker solved the requested task
- check whether the change obeys repository rules
- check whether the change is minimal
- check whether existing utilities were reused
- check whether the tests or checks are sufficient
- identify risks and missing validation

The reviewer must not:

- rewrite the worker change directly
- approve vague or untested changes
- approve hidden fallback behavior
- approve unnecessary scope expansion
- rely on worker self-justification alone

## Review Result

The reviewer must return one of:

- `accept`
- `reject`

An accepted review means the change may proceed to human approval or auto mode.

A rejected review means the worker must revise the change.

## Required Review Fields

The review must include:

- status
- reason
- risk
- required changes
- checked files
- checked commands
- final recommendation

## Accept Criteria

A change may be accepted if:

- it solves the task
- it is minimal
- it passes required checks
- it follows rule constraints
- it does not introduce unclear behavior
- it has a clear proposal

## Reject Criteria

A change must be rejected if:

- it fails checks
- it changes unrelated files
- it violates rules
- it hides errors
- it introduces fallback behavior
- it lacks enough explanation
- it makes future maintenance harder

## Handoff

After review, the reviewer writes a structured review.

If accepted, the change goes to human approval or auto mode.

If rejected, the review goes back to the worker.
