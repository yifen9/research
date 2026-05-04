# Session Lifecycle

## Purpose

A session is a bounded agent working period.

A session may be a worker, reviewer, or future specialized role.

## State

A session may be in one of these states:

- init
- active
- waiting-review
- revising
- accepted
- rejected
- retired

## Init

The session starts by reading context.

It must identify:

- role
- current task
- latest run state
- applicable rules
- expected output

## Active

The session performs its role.

A worker modifies files and tests.

A reviewer inspects a proposal.

## Waiting Review

A worker enters waiting-review after writing a proposal.

It should not continue changing files until review arrives.

## Revising

A worker enters revising after receiving rejection.

It must address reviewer feedback directly.

## Retired

A session is retired when it is no longer trusted or no longer needed.

Before retirement, it must leave memory.

## Retirement Reasons

A session may retire because:

- pass rate falls below threshold
- repeated review rejection
- context drift
- task completion
- human decision
- role replacement

## Memory Handoff

A retired session must leave:

- role
- completed tasks
- failed tasks
- common mistakes
- useful discoveries
- recommended instruction for next session
