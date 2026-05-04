# Rule Manifest

## Purpose

This directory contains agent-readable rule documents generated from rule YAML files.

## Source

- rule_dir: rule
- target: context/rule

## Read Order

- [Code](./code.md)
- [Name](./name.md)
- [File](./file.md)
- [Config](./config.md)
- [Design](./design.md)
- [Agent](./agent.md)
- [Word](./word.md)

## Rule

- YAML files under rule/ are the source of truth.
- Markdown files under context/rule/ are generated.
- Do not edit context/rule/*.md manually.
- Update rule/*.yaml first, then rerun context-rule-write.
