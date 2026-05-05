# Session Lifecycle

## State

- active
- closed
- retired

## Close Order

- Write memory.
- Write summary.
- Write handoff if needed.
- Write close metadata.
- Update role memory.
- Update role handoff if handoff exists.
- Run session check.

## Rule

- Session runtime lives under `out/agent/session/`.
- Closed sessions must have memory.
- Role memory lives under `out/agent/memory/`.
- Role handoff lives under `out/agent/handoff/`.
