# Auto Mode

## Purpose

Auto mode allows low-risk accepted changes to be committed without manual approval.

Auto mode must be explicitly enabled in:

```text
config/agent.yaml
```

## Enable

Set:

```yaml
agent:
  mode: auto
```

## Gate

Auto mode uses the configured auto gate:

```yaml
agent:
  gate:
    auto:
      - just fmt
```

The gate can later include stricter commands:

```yaml
agent:
  gate:
    auto:
      - just fmt
      - just rule-check
```

## Required Conditions

Auto mode requires:

- change status is accepted
- risk is allowed by config
- configured auto gates pass
- git has changes to commit
- task is not forbidden by config

## Forbidden by Default

Auto mode should reject:

- rule changes
- workflow changes
- architecture changes
- medium-risk changes
- high-risk changes
- failed gates

## Flow

Create sessions:

```bash
just s-agent-session-new worker
just s-agent-session-new reviewer
```

Create change:

```bash
just s-agent-change-new-latest "Fix one small issue"
```

Generate context:

```bash
just s-agent-context-write-latest
```

Run worker:

```bash
just s-agent-run-worker-latest
```

Regenerate context:

```bash
just s-agent-context-write-latest
```

Run reviewer:

```bash
just s-agent-run-reviewer-latest
```

Record accepted review:

```bash
just s-agent-change-review-latest accept low
```

Commit automatically:

```bash
just s-agent-change-auto-latest
```

## Result

A successful auto run updates:

```text
out/agent/change/<change-id>/result.yaml
```

with:

```yaml
human: auto
status: committed
commit: <hash>
```

## Rule

Auto mode is only for low-risk mechanical changes.

If the change affects architecture, rule, workflow, research claim, or publication content, use human mode.
