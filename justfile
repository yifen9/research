set shell := ["bash", "-lc"]

env-dev := "set -a; source config/env/.dev.env; set +a;"

default:
    just --list

init:
    just py-doctor

check:
    just py-check
    just q-check

py-doctor:
    just py-venv
    just py-sync

py-venv:
    {{env-dev}} mkdir -p out/temp/python/egg-info && (test -d "$UV_PROJECT_ENVIRONMENT" || uv venv "$UV_PROJECT_ENVIRONMENT")

py-sync:
    {{env-dev}} VIRTUAL_ENV= uv sync --all-packages

py-sync-lock:
    {{env-dev}} VIRTUAL_ENV= uv sync --locked --all-packages

py-fmt:
    just py-sync
    {{env-dev}} VIRTUAL_ENV= uv run ruff format .

py-fmt-check:
    {{env-dev}} VIRTUAL_ENV= uv run ruff format --check .

py-lint:
    {{env-dev}} VIRTUAL_ENV= uv run ruff check . --fix

py-lint-check:
    {{env-dev}} VIRTUAL_ENV= uv run ruff check .

py-check:
    just py-fmt-check
    just py-lint-check
    just py-compile

py-compile:
    {{env-dev}} VIRTUAL_ENV= uv run python -m compileall src

q-check:
    quarto check

q-preview:
    quarto preview --render all

q-render:
    quarto render
