# Meta

## Purpose

Meta fields make project artifacts safe to audit across parallel roles, sessions, runs, and branches.

## Field

- id
- project
- kind
- state
- role
- session
- run
- branch
- base
- commit
- target
- created
- updated

## Rule

- Source artifact version is the git commit.
- Runtime execution version is the run path under `out/run/`.
- Actor version is the session id under `out/agent/session/`.
- Parallel work uses scoped branches.
- Artifact metadata must record the branch that owns the work.
