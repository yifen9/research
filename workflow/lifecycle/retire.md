# Retire

## Purpose

Retirement prevents low-quality or context-drifted sessions from continuing.

A worker is not permanent.

## Metric

Each worker should track:

- task count
- accepted count
- rejected count
- pass rate
- recent pass rate
- retirement threshold

## Default Threshold

The default pass-rate threshold is 50 percent.

If recent pass rate is below the threshold, the worker should retire.

## Review Window

The review window should contain enough tasks to be meaningful.

The default window is 6 tasks.

## Retirement Trigger

A worker may retire when:

- recent pass rate is below threshold
- reviewer rejects repeated revisions
- human requests retirement
- the task domain changes too much
- context becomes stale

## Retirement Memory

Before retirement, the worker must write memory.

The memory must include:

- what worked
- what failed
- repeated mistakes
- useful repository knowledge
- next worker recommendation

## New Worker

A new worker should read:

- context/index.md
- latest run summary
- previous worker memory
- active task
