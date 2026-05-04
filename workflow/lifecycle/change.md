# Change Lifecycle

## Purpose

A change is one proposed repository modification.

Each change should be small, reviewable, testable, and commit-ready.

## State

A change may be in one of these states:

- draft
- proposed
- reviewed
- accepted
- rejected
- committed
- discarded

## Draft

The worker is editing files and running checks.

No reviewer decision exists yet.

## Proposed

The worker has produced a proposal.

The proposal must include changed files, commands, results, and risks.

## Reviewed

The reviewer has inspected the proposal and diff.

The review must return accept or reject.

## Accepted

The reviewer accepts the change.

The change may proceed to human approval or auto mode.

## Rejected

The reviewer rejects the change.

The worker must revise or the change must be discarded.

## Committed

The change has been committed to Git.

The commit hash must be recorded.

## Discarded

The change is abandoned.

The reason should be recorded.

## Rule

A change should not mix unrelated tasks.

A change should not be committed without traceable proposal and review.
