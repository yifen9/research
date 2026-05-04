# File

## Source

- source: rule/file.yaml

## Content

```yaml
file:
  root:
  - rule
  - infra
  - script
  - template
  - context
  - include
  - build
  prefer:
    config:
    - yaml
    - toml
    - json
  deny:
  - scripts
  - templates
  - rules
  - configs
```
