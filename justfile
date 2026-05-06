set shell := ["bash", "-lc"]

runtime := "set -a; source config/runtime/dev.env; set +a;"
secrets := "set -a; [ ! -f .env ] || source .env; set +a;"

default:
    just --list

init:
    just opencode-doctor
    just py-doctor
    just graphify-doctor

opencode-doctor:
    mkdir -p /home/vscode/.config/opencode/skills/feynman
    install -m 0644 config/external/opencode/skills/feynman/SKILL.md /home/vscode/.config/opencode/skills/feynman/SKILL.md

check:
    just py-check
    just q-check

py-doctor:
    just py-venv
    just py-sync

py-venv:
    {{runtime}} mkdir -p out/temp/python/egg-info && (test -d "$UV_PROJECT_ENVIRONMENT" || uv venv "$UV_PROJECT_ENVIRONMENT")

py-sync:
    {{runtime}} VIRTUAL_ENV= uv sync --all-packages

py-sync-lock:
    {{runtime}} VIRTUAL_ENV= uv sync --locked --all-packages

graphify-doctor:
    {{runtime}} mkdir -p "$UV_TOOL_BIN_DIR" "$UV_TOOL_DIR"
    {{runtime}} uv tool install graphifyy==0.7.8 --with openai
    {{runtime}} "$UV_TOOL_BIN_DIR"/graphify --help >/dev/null

graphify-nav:
    {{runtime}} mkdir -p out/temp/graphify
    {{runtime}} {{secrets}} "$UV_TOOL_BIN_DIR"/graphify extract . --out out/temp/graphify
    {{runtime}} "$UV_TOOL_BIN_DIR"/graphify tree --graph out/temp/graphify/graphify-out/graph.json --root . --output out/temp/graphify/graphify-out/GRAPH_TREE.html --label research
    python3 -c "from pathlib import Path; import shutil; path = Path('graphify-out'); path.exists() and shutil.rmtree(path)"

py-fmt:
    just py-sync
    {{runtime}} VIRTUAL_ENV= uv run ruff format .

py-fmt-check:
    {{runtime}} VIRTUAL_ENV= uv run ruff format --check .

py-lint:
    {{runtime}} VIRTUAL_ENV= uv run ruff check . --fix

py-lint-check:
    {{runtime}} VIRTUAL_ENV= uv run ruff check .

py-check:
    just py-fmt-check
    just py-lint-check
    just py-compile

py-compile:
    {{runtime}} VIRTUAL_ENV= uv run python -m compileall src

q-check:
    quarto check
    quarto render doc/quarto
    python3 -c "from pathlib import Path; import shutil; src = Path('doc/quarto/.quarto'); dst = Path('out/temp/quarto/.quarto'); dst.parent.mkdir(parents=True, exist_ok=True); shutil.rmtree(dst, ignore_errors=True); src.exists() and shutil.move(str(src), str(dst))"
