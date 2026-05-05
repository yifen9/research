set shell := ["bash", "-lc"]

default:
    just --list

init:
    just py-doctor
    just o-doctor
    just q-doctor

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

s-rule-check:
    uv run python script/rule/check.py .

s-infra-docker-write:
    uv run python script/infra/docker/write.py . full

s-context-write:
    just s-context-profile-user-write
    just s-context-run-write
    just s-context-rule-write
    just s-context-project-write
    just s-context-agent-write
    just s-context-index-write

s-context-profile-user-write:
    uv run python script/context/profile/user/write.py . https://github.com/yifen9/yifen9.li/archive/refs/heads/main.zip out/temp/source/profile/user context/profile/user

s-context-run-write:
    uv run python script/context/run/write.py . out/run context/run 64

s-context-rule-write:
    uv run python script/context/rule/write.py . rule context/rule

s-context-project-write:
    uv run python script/context/project/write.py . context/project 4

s-context-index-write:
    uv run python script/context/index/write.py . context

o-doctor:
    opencode --version

q-doctor:
    quarto check
    quarto --version

q-preview:
    quarto preview

q-preview-render:
    quarto preview --render all

q-render:
    quarto render

q-clean:
    rm -rf build .quarto

q-rebuild:
    just q-clean
    just q-render
