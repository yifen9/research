# Patch Artifact

## Purpose

A patch artifact stores the worker's proposed repository modification as a standard unified diff.

The patch must be reviewable, checkable, applicable, and reversible.

## File

A change may contain:

```text
patch.diff
```

## Format

The patch must use standard unified diff format.

It must be compatible with:

```bash
git apply --check patch.diff
git apply patch.diff
```

## Responsibility

The worker should produce a patch when repository files need to be modified.

The worker must not rely only on natural language when a concrete file change is required.

## Required Rule

A patch must:

- be minimal
- match the task scope
- avoid unrelated files
- avoid generated runtime artifacts
- avoid hidden files
- avoid fallback behavior
- avoid secrets or credentials

## Forbidden Path

A patch must not modify:

- `.git/`
- `out/`
- `.venv/`
- `.ruff_cache/`
- `__pycache__/`

## Check

Before applying, the patch must pass:

```bash
git apply --check patch.diff
```

## Apply

After applying, the configured gate must pass.

The applied state must be recorded in `result.yaml`.

## Handoff

After a patch is applied, the worker proposal and patch should be reviewed by the reviewer.

The reviewer should inspect both the natural-language proposal and the actual diff.
