# Research Repository Instructions

This repository is the parent infrastructure for research work. OpenCode is the active agent runtime for new interactive work.

## Current Phase

- Phase 1 installs and configures OpenCode in the devcontainer.
- Phase 2 will implement the architect, task, worker, reviewer, sandbox, and project export workflow.

## Active Context

- Use `workflow/`, `rule/`, `context/`, and `script/context/` as governance and context sources.
- Use `src/research/util/` and `src/research/io/` as reusable infrastructure utilities.
- Treat `out/` as generated runtime output, not as canonical instructions.

## Inactive Legacy Path

- Do not use custom Gemini/API provider scripts. That execution path was removed in favor of OpenCode.
- Do not recreate provider-specific credentials or committed API-key configuration.

## Safety

- Do not commit without an explicit user request.
- Do not change rule, workflow, architecture, or research claims through automatic approval.
- Keep project-specific research work under a future `project/<slug>` boundary.
