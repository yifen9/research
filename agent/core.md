# Core Doctrine

## Scope

- This repository is the control system for personal research automation infrastructure.
- The system should approach full automation across idea discovery, topic formation, proposal writing, recursive planning, experiment execution, report generation, repository release, maintenance, and public presentation.
- The intended operating hierarchy is human above AI, AI above mechanical scripts. Higher layers should spend asymptotically less mental effort maintaining lower layers.
- Quality outranks throughput. Reject weak work rather than accumulating low-quality complexity.
- The system should become easier to operate as it grows older.

## Principle

- Prefer the smallest complete system that can be inspected, reproduced, versioned, and replaced.
- Make role, mode, state, approval, path, backend, and command boundaries explicit.
- Keep every component replaceable through configuration and command contracts.
- Avoid hidden behavior, magic constants, implicit state, silent fallback, and unrecorded decisions.
- Continuously review completed work, summarize current state, forecast risk, and offer bounded next choices.

## Foundation

- Use `config/rule/` as the governance source of truth.
- Use `config/template/` as reusable template source.
- Use `config/agent.yaml` to select the active agent backend and vector backend.
- Use `agent/workflow/` for role, session, lifecycle, artifact, and command contracts.
- Use `agent/backend/<name>/manifest.yaml` and `agent/backend/<name>/template/` for backend-specific configuration source.
- Keep generated backend root configuration ignored by git and reproducible from the active backend template.

## Naming

- Every directory, file, function, argument, and vocabulary item must carry semantic meaning.
- The vocabulary should be minimal, controlled, and mechanically checked.
- A reader should infer purpose and boundary from path, file name, function name, and argument structure.
- Directory and file boundaries must preserve decoupling, explicit responsibility, clear semantics, and mechanical maintainability.
- Prefer reuse over duplication. Add new words only when existing vocabulary cannot express the intended meaning.

## Reproducibility

- The devcontainer is the baseline reproducible environment.
- Entering the environment should recreate the complete development context without drift.
- Package managers and explicit configuration should control variable inputs.
- Function arguments should be explicit. Default parameters are forbidden unless values are provided through explicit external configuration.
- Runtime behavior should avoid implicit state and resemble functional data flow where practical.
- Required infrastructure must fail fast when unavailable.

## Audit

- Every atomic step should be recorded at the appropriate layer.
- Audit records should be hierarchical: high-level summaries must be skimmable, while lower layers must permit detailed inspection.
- Every dialogue round should be recorded completely, redacted according to configuration, and ingested into cross-session memory through the configured vector backend.
- `message.jsonl` is the append-only dialogue journal. The vector backend is a derived semantic index, not the source of truth.
- Session context must remain constrained and robust. Memory and handoff are mandatory continuity artifacts.

## Version

- Every input that can change output must be versioned or otherwise represented by sufficient metadata for reproduction.
- Version metadata should be readable by humans, AI, and mechanical scripts.
- Git should be used aggressively for small, atomic approved changes.
- The intended branch hierarchy is `main`, `dev`, `feature-*`, and `test-*`.
- `main` means production-ready, `dev` means continuous development, `feature-*` means new feature work, and `test-*` means uncertain work.
- Lower branches merge upward after validation.
- Approved durable governance, workflow, backend, and rule changes require explicit approval and commits.

## Minimal Set

- Repeatedly audit every parameter, function, file, directory, feature, subsystem, and system boundary.
- Ask whether each item can be abstracted, reused, removed, automated, or made cheaper to maintain.
- Add only durable artifacts that have a clear owner, path, command contract, and review path.
- Mechanical scripts should handle anything deterministic.
- AI should continuously ask whether a mechanical abstraction can replace AI work.

## Layout

- `agent` contains AI-related control files.
- `config` contains parameter templates, rules, and reusable templates.
- `infra` contains infrastructure outside the repository core, including Docker and DevOps surfaces.
- `out` contains audit and test artifacts, usually runtime output that may be cleared.
- `src` contains reusable internal code across contexts.
- `script` contains specific executable entrypoints for particular purposes.
- `justfile` is the orchestration layer for human and AI command use.
- `doc` contains the Quarto site source.
- `project` is the main research workspace.

## AI

- Planning, decisions, and plans outrank execution.
- Uncertainty must be surfaced explicitly. Macro-level choices require extra caution and bounded options.
- Human dialogue is Chinese by default. Durable repository artifacts are English by default.
- The human should usually receive bounded choices rather than open-ended questions.
- Architect identity overrides backend identity during role chat.
- AI should maintain conversation templates, output templates, initial prompts, and its own self-improvement loop.
- AI should use templates whenever practical and should be responsible for its own quality control.
- Tests and checks should be strong enough that delivery does not rely on optimism.

## Session

- Architect chat is the default human entry path.
- Every backend conversation session must attach to an architect session before durable conversation recording.
- Auto capture must bind a backend session key to exactly one active architect session or fail loudly with repair choices.
- Multiple active architect sessions without an existing backend binding are ambiguous and must not be guessed.
- Bound closed, retired, missing, or duplicate sessions are invalid and must not silently fall back.
- Every recorded round must be appended to `message.jsonl` and ingested into the vector backend.
- Sessions should support robust continuation, rotation, and handoff when context, topic, budget, or message limits require transfer.

## Mode

- Session mode must be explicit when work exceeds simple chat.
- Full research mode moves from idea to proposal, recursive decomposition, experiment, report, release, and maintenance.
- Autopilot mode continues scoped low-risk work until a stop condition appears.
- Scout mode explores progress, risks, refactors, optimizations, features, and new project ideas without changing artifacts.
- Governance mode maintains rules, workflow, backend, config source, and checks after explicit approval.
- Repair mode fixes failing checks within a scoped boundary.
- Modes must define purpose, allowed paths, denied paths, confirmation gates, required checks, stop conditions, and output type.

## Permission

- Directory sensitivity defines risk boundaries.
- `src` is more sensitive than `script`, and `script` is more sensitive than `justfile`.
- AI must assess risk before edits and respect mode permissions.
- Future modes may grant broader permissions only when explicitly selected.
- Governance, workflow, backend manifest, backend template, and rule changes require architect-level approval.

## Research

- The mother repository may manage multiple projects.
- Each project may contain multiple repositories.
- Repositories and projects may be frozen, released, published, and maintained automatically.
- A Quarto site should expose projects, reports, releases, and metadata at multiple detail levels for public presentation.
- Proposals, experiments, and reports should support recursive hierarchical decomposition until work becomes mechanically executable.

## Check

- Philosophical rules should become mechanical enforcement wherever possible.
- Convert doctrine into registries, schemas, rule checks, tests, CI gates, audit commands, backend checks, session checks, and release checks.
- Run rule, backend, session, compile, and targeted tests before treating workflow changes as complete.
- Keep tests close to command and artifact behavior.
- Surface pre-existing failures separately from changes made in the current work.
