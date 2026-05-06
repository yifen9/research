set shell := ["bash", "-lc"]

default:
    just --list

init:
    just py-doctor
    just s-agent-backend-write
    just s-agent-backend-check
    just s-rule-check
    just doc-check

py-doctor:
    just py-venv
    just py-sync

py-venv:
    test -d .venv || uv venv

py-sync:
    uv sync --all-packages

py-sync-lock:
    uv sync --locked --all-packages

py-up:
    uv lock --upgrade

py-add PKG:
    uv add {{PKG}}

py-add-dev PKG:
    uv add --dev {{PKG}}

py-rm PKG:
    uv remove {{PKG}}

py-rm-dev PKG:
    uv remove --dev {{PKG}}

py-fmt:
    just py-sync
    uv run ruff format .

py-fmt-check:
    uv run ruff format --check .

py-lint:
    uv run ruff check . --fix

py-lint-check:
    uv run ruff check .

py-test:
    uv run python -m unittest discover -s test

py-compile:
    uv run python -m compileall src script test

s-rule-check:
    uv run python script/rule/check.py .

s-agent-backend-write:
    uv run python script/agent/backend/write.py .

s-agent-backend-check:
    uv run python script/agent/backend/check.py .

s-agent-session-check:
    uv run python script/agent/session/check.py .

doc-check:
    quarto check
    quarto render doc

doc-render:
    quarto render doc
