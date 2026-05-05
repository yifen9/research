# Auto Mode

## Purpose

Auto mode is deferred during Phase 1.

The repository is moving from the custom Gemini/API runner to OpenCode. Until the Phase 2 architecture is implemented, automatic commits must not drive research, workflow, rule, architecture, publication, or export changes.

## Current Status

OpenCode is the active agent runtime.

The old provider-backed auto path has been removed from the active command surface.

## Allowed Automation

Automation may still run local checks such as:

- `just fmt-check`
- `just lint-check`
- `just s-rule-check`
- `just q-render`

Automation may prepare evidence, but it must not commit without explicit human approval.

## Future Phase

Phase 2 may reintroduce automatic progression only after these exist:

- structured task ledger
- sandboxed worker attempts
- reviewer decision artifact
- architect decision artifact
- explicit risk policy
- passing gate records
- commit hash recording

## Rule

When in doubt, use human mode.
