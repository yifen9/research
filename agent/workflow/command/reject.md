# Reject Command

## Purpose

Reject commands record a durable rejection and reason.

## Rule

- Rejection must include reason.
- Rejection must not silently delete audit evidence.
- If rejected work is uncommitted, rollback is target-scoped.
- If rejected work is committed, rollback uses a revert commit rather than history rewrite.
- Higher roles decide merge, rebase, or abandon for scoped branches.
