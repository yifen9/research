# Code

## Source

- source: rule/code.yaml

## Content

```yaml
code:
  arg:
    default: false
    explicit: true
  name:
    max_word: 2
  nest:
    max: 4
  file:
    max_line: 1024
  style:
    comment: false
    doc: false
  reuse:
    prefer: true
    duplicate: false
  fallback:
    allow: false
```
