# Result Artifact

## Purpose

A result artifact records the final outcome of a change.

It links task, proposal, review, command results, and commit state.

## Required Fields

A result should include:

- change id
- task
- worker
- reviewer
- status
- commit hash
- run summary
- final decision

## Status

Status may be:

- accepted
- rejected
- committed
- discarded
- returned

## Commit Hash

If committed, the result must include the commit hash.

If not committed, the result must explain why.

## Trace

A result should link to:

- task artifact
- proposal artifact
- review artifact
- run summary
- relevant commit

## Rule

A result should be written for every reviewed change.
