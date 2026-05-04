# Rule Context

## Code

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

## Name

```yaml

name:
  case:
    python: snake
    file: kebab
    dir: kebab
    yaml: snake
  number:
    dir: single
    file: single
    module: single
  word:
    source: rule/word
    strict: true
  allow:
  - .git
  - .github
  - .devcontainer
  - README.md
  - LICENSE
  - Dockerfile
  - justfile
  - _quarto.yaml

```

## File

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

## Config

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

## Design

```yaml

design:
  reuse:
    prefer: true
    duplicate: false
  fallback:
    allow: false
  explicit:
    require: true
  hidden:
    allow: false
  magic:
    allow: false
  fail:
    silent: false
    loud: true

```

## Agent

```yaml

agent:
  code:
    obey: rule/code.yaml
  name:
    obey: rule/name.yaml
  file:
    obey: rule/file.yaml
  config:
    obey: rule/config.yaml
  design:
    obey: rule/design.yaml
  word:
    obey: rule/word
  change:
    new_word: false
    new_rule: false
    silent: false
  output:
    comment: false
    extra: false

```

## Word

### Act

```yaml

word:
- add
- build
- check
- clean
- copy
- fetch
- init
- list
- load
- make
- push
- read
- render
- scan
- sync
- test
- update
- write

```

### Core

```yaml

word:
- act
- agent
- build
- code
- conf
- config
- context
- core
- data
- dev
- doc
- file
- full
- image
- infra
- input
- lang
- name
- output
- part
- profile
- project
- repo
- rule
- script
- site
- task
- template
- tool
- word

```

### File

```yaml

word:
- docker
- compose
- quarto
- latex
- python
- julia
- rust
- r
- yaml
- toml
- json
- qmd
- md
- css
- scss
- git
- github
- readme
- license
- just
- justfile

```

### Py

```yaml

word:
- allow
- any
- append
- arg
- argv
- ast
- audit
- bad
- base
- best
- body
- buffer
- byte
- check
- child
- code
- comp
- config
- conf
- console
- context
- count
- csv
- current
- data
- date
- default
- depth
- dir
- doc
- docker
- emit
- encoding
- ensure
- env
- error
- eta
- event
- except
- extra
- field
- file
- finger
- folder
- header
- hasher
- index
- io
- item
- json
- jsonl
- key
- kind
- label
- level
- limit
- line
- list
- load
- logger
- main
- make
- map
- max
- message
- meta
- name
- nest
- node
- output
- page
- parquet
- param
- part
- path
- payload
- pct
- pool
- pq
- prev
- print
- profile
- progress
- reader
- record
- rel
- remain
- root
- rotate
- row
- rows
- rule
- scan
- segment
- seen
- sha
- sink
- size
- skip
- start
- status
- stem
- style
- table
- target
- temp
- text
- time
- title
- total
- trace
- transient
- tree
- value
- word
- write
- writer
- yaml

```
