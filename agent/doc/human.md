# Human Mode

## Purpose

Human mode is the default agent workflow.

In this mode, the worker performs the task, the reviewer inspects the result, and the human explicitly approves before commit.

## Start

Create one worker session:

```bash
just s-agent-session-new worker
```

Create one reviewer session:

```bash
just s-agent-session-new reviewer
```

A session can be reused across multiple changes until it is retired.

## Create Change

Create a change with the latest active worker:

```bash
just s-agent-change-new-latest "Fix one small issue"
```

This creates:

```text
out/agent/change/<change-id>/
  task.md
  proposal.md
  review.md
  result.yaml
```

Edit `task.md` before assigning the task if the objective is still incomplete.

## Build Context Bundle

Generate a bundle for worker and reviewer:

```bash
just s-agent-context-write-latest
```

This creates:

```text
out/agent/context/<bundle-id>/
  _manifest.md
  worker.md
  reviewer.md
```

## Run Worker

Run the worker agent on the latest bundle and latest change:

```bash
just s-agent-run-worker-latest
```

The worker output is written to:

```text
out/agent/change/<change-id>/proposal.md
out/agent/change/<change-id>/worker.md
```

The worker should not approve or commit its own change.

## Run Reviewer

Regenerate the context bundle after the worker finishes:

```bash
just s-agent-context-write-latest
```

Run the reviewer:

```bash
just s-agent-run-reviewer-latest
```

The reviewer output is written to:

```text
out/agent/change/<change-id>/review.md
out/agent/change/<change-id>/reviewer.md
```

## Record Review

If the reviewer accepts with low risk:

```bash
just s-agent-change-review-latest accept low
```

If the reviewer rejects:

```bash
just s-agent-change-review-latest reject medium
```

This updates:

```text
out/agent/change/<change-id>/result.yaml
out/agent/session/<worker-id>/state.yaml
```

## Approve and Commit

If the change is accepted and the human approves:

```bash
just s-agent-change-approve-latest
```

This runs the configured human approval gates from:

```text
config/agent.yaml
```

Then it commits and writes the commit hash to:

```text
out/agent/change/<change-id>/result.yaml
```

## Retire Session

Retire the latest worker:

```bash
just s-agent-session-retire-latest worker "context drift"
```

Retire the latest reviewer:

```bash
just s-agent-session-retire-latest reviewer "reviewer replacement"
```

A retired session should leave memory in:

```text
out/agent/session/<session-id>/memory.md
```

## Smoke Test

Run:

```bash
just s-agent-smoke-human
```

This checks whether the current human-mode agent workflow has the required sessions, change, bundle, config, and result state.

## Rule

Human mode must be used for:

- architecture changes
- rule changes
- workflow changes
- medium-risk changes
- high-risk changes
- ambiguous reviewer output
