# Review Artifact

## Purpose

A review is the reviewer decision on a worker proposal.

It must be structured enough for the worker, human, and future agents to understand.

## Required Fields

A review must include:

- status
- reason
- risk
- checked files
- checked commands
- required changes
- final recommendation

## Status

Status must be one of:

- accept
- reject

## Risk

Risk must be one of:

- low
- medium
- high

## Accept Review

An accept review should explain why the change is safe enough to proceed.

It may still include notes for human attention.

## Reject Review

A reject review must explain what needs to change.

It should be specific and actionable.

## Required Changes

Required changes should be written as direct instructions.

The worker should be able to revise based on them.

## Rule

The reviewer must not approve a change only because the worker says it works.

The reviewer must inspect evidence.
