# Auto Mode

## Purpose

Auto mode allows low-risk changes to be committed without manual approval.

Auto mode is disabled unless explicitly enabled.

## Flow

1. Worker performs the task.
2. Worker runs required checks.
3. Worker writes proposal.
4. Reviewer inspects proposal and diff.
5. Reviewer accepts the change.
6. Risk must be low.
7. Required checks must pass.
8. The system creates one commit.
9. The result is recorded.

## Required Conditions

Auto mode requires:

- reviewer status is accept
- risk is low
- checks pass
- no architecture change
- no rule change
- no workflow change
- no publication or research claim change
- no secret or credential change

## Forbidden Cases

Auto mode must not be used for:

- architecture redesign
- rule modification
- agent governance changes
- external dependency changes
- large refactoring
- ambiguous failures
- failed or skipped checks

## Commit

Each auto-mode change must create exactly one commit.

The commit must be traceable to the proposal, review, and run summary.
