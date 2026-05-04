# Run Manifest

## Purpose

This directory summarizes recent execution state for agents.

## File

- [Latest](./latest.md)
- [Recent](./recent.md)

## Source

- run_dir: out/run
- target: context/run
- limit: 16

## Rule

- Read latest.md first.
- Use recent.md only when recent history matters.
- Full audit artifacts remain under out/run.
- Do not edit context/run/*.md manually.
- Regenerate this directory with context-run-write.
