# Human Mode

## Purpose

Human mode is the active Phase 1 workflow.

In this mode the human works with OpenCode inside the devcontainer. Repository scripts keep rules, context, run records, and review artifacts available, but custom Gemini/API worker and reviewer execution is no longer active.

## Start

Enter the devcontainer and verify OpenCode:

```bash
just o-doctor
```

Start the terminal UI:

```bash
just o-tui
```

Or start a headless server for API or remote clients:

```bash
just o-serve
```

## Context

OpenCode should use `AGENTS.md` as the first project instruction file.

Useful repository context remains in:

- `context/index.md`
- `context/project/_manifest.md`
- `context/rule/_manifest.md`
- `context/workflow/`
- `workflow/`

Generated runtime artifacts under `out/` are evidence, not instructions.

## Phase 1 Boundary

Phase 1 provides OpenCode readiness and removes the old provider-backed runner path.

Phase 1 does not implement the final architect, task DAG, sandbox, reviewer, project export, or downstream sync workflow.

## Preserved Control Plane

The following artifact systems remain for Phase 2:

- session records
- change records
- review records
- patch checks
- approval gates
- run audit summaries

## Forbidden Legacy Path

Do not use or recreate:

- committed provider API keys
- `config/provider.yaml`
- custom Gemini provider code
- provider-backed worker or reviewer scripts
- provider-backed automatic task drafting

## Rule

Human approval remains required for architecture, workflow, rule, research claim, publication, and export changes.
