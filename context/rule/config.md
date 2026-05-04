# Config

## Source

- source: rule/config.yaml

## Content

```yaml
config:
  rank:
  - yaml
  - toml
  - json
  yaml:
    main: true
  toml:
    allow: true
  json:
    api: true
    hand: false
    allow:
    - devcontainer.json
    - package.json
    - tsconfig.json
```
