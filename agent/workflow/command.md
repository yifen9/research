# Command

## Backend Write

- Backend write renders root backend config from the active backend template.
- Backend write reads `config/agent.yaml` for the active backend name.

## Backend Check

- Backend check verifies rendered root backend config matches the active backend template.
- Backend check fails when active backend source or rendered config is missing.

## Session New

- Session new creates an active session artifact.
- Session new connects to the configured vector backend before the session is accepted.
- Session new writes the active initial context and mode guidance.

## Session Message

- Session message appends a redacted message event to `message.jsonl`.
- Session message ingests the message into the configured vector backend.

## Session Heartbeat

- Session heartbeat verifies vector entries for recorded messages.
- Session heartbeat repairs missing message vector entries.

## Session Sync

- Session sync ingests recorded messages that are missing from the vector backend.

## Session Check

- Session check verifies session artifacts and vector coverage.

## Close

- Close ends an active session.
- Close writes memory before terminating.
- Close memory follows `config/template/agent/memory.md`.

## Rotate

- Rotate transfers an active session to a new session of the same role.
- Rotate writes memory and handoff before terminating the old session.
- Rotate handoff follows `config/template/agent/handoff.md`.

## Retire

- Retire removes a mistaken session.
- Retire records the reason for retirement.
