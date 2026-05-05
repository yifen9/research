# Decision

## Purpose

Decision artifacts record explicit approval, rejection, or amendment.

## Field

- id
- target
- actor
- role
- decision
- reason
- time
- run
- branch
- commit

## Rule

- Approval must be represented as a decision artifact.
- Chat alone is not a durable approval.
- Approved decisions require a git commit.
