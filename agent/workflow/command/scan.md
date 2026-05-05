# Scan Command

## Purpose

Scan commands summarize project artifacts for architect status reporting.

## Rule

- Scan reads project artifacts and writes only run output.
- Scan does not mutate project source.
- Architect uses scan before summarizing manager, worker, or reviewer state.
