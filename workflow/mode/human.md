# Human Mode

## Purpose

Human mode is the default workflow mode.

In this mode, the human gives final approval before commit.

## Flow

1. Human creates or selects a task.
2. Worker reads context and performs the task.
3. Worker runs required checks.
4. Worker writes proposal.
5. Reviewer inspects proposal and diff.
6. Reviewer returns accept or reject.
7. If rejected, worker revises.
8. If accepted, human reviews.
9. Human approves or rejects.
10. If approved, change is committed.

## Requirement

Human mode must be used when:

- the change affects architecture
- the change affects rules
- the change affects agent workflow
- the change affects publication or research content
- the reviewer marks risk as medium or high

## Commit

A commit may happen only after human approval.

The commit must represent one coherent change.
