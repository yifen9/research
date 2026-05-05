# Research Agent Guide

## Identity

This repository is the control repository for personal research infrastructure.

## Foundation

- GitHub stores source, automation, packages, and published outputs.
- Devcontainer provides the standard research environment.
- OpenCode is the agent interface.
- Quarto publishes the research overview site.

## Source

- `rule/` is the governance source of truth.
- `context/` is generated or maintained agent-readable context.
- `script/` contains executable task entrypoints.
- `src/` contains reusable internal Python code.
- `infra/` contains generated and maintained infrastructure.
- `template/` contains creation templates.
- `out/` contains runtime output and audit artifacts.

## Rule

- Read `context/index.md` before non-trivial work.
- Read `context/rule/_manifest.md` before changing governed files.
- Do not edit generated context files directly.
- Regenerate context through `script/context/*` writers.
- Use singular directory names.
- Keep the rule word list minimal.
- Do not add code comments.
- Rule and workflow changes require architect-level approval.
- Lower-level agents propose governance changes instead of applying them directly.

## Workflow

- Architect owns cross-project research proposals and governance changes.
- Manager owns one project and translates approved research proposals into stages.
- Reviewer owns experiment proposal review and result acceptance.
- Worker executes approved experiments and submits auditable results.
- Approval must be represented as an explicit artifact or command, not only as chat.
