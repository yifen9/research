set shell := ["bash", "-lc"]

default:
    just --list

init:
    just py-doctor
    just s-agent-backend-write
    just s-agent-backend-check
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

s-agent-backend-write:
    uv run python script/agent/backend/write.py .

s-agent-backend-check:
    uv run python script/agent/backend/check.py .

s-agent-session-new ROLE TOPIC:
    uv run python script/agent/session/new.py . {{ROLE}} {{TOPIC}}

s-agent-session-close ROLE ID MEMORY SUMMARY:
    uv run python script/agent/session/close.py . {{ROLE}} {{ID}} {{MEMORY}} {{SUMMARY}}

s-agent-session-rotate ROLE ID MEMORY SUMMARY HANDOFF TOPIC:
    uv run python script/agent/session/rotate.py . {{ROLE}} {{ID}} {{MEMORY}} {{SUMMARY}} {{HANDOFF}} {{TOPIC}}

s-agent-session-retire ROLE ID REASON:
    uv run python script/agent/session/retire.py . {{ROLE}} {{ID}} {{REASON}}

s-agent-session-check:
    uv run python script/agent/session/check.py .

s-agent-handoff-write ROLE TEXT:
    uv run python script/agent/handoff/write.py . {{ROLE}} {{TEXT}}

s-agent-memory-write ROLE TEXT:
    uv run python script/agent/memory/write.py . {{ROLE}} {{TEXT}}

s-project-bench-check SLUG EXPERIMENT METRIC:
    uv run python script/project/bench/check.py . {{SLUG}} {{EXPERIMENT}} {{METRIC}}

s-project-data-add BASE:
    uv run python script/project/data/add.py . {{BASE}}

s-project-data-check:
    uv run python script/project/data/check.py .

s-project-data-scan:
    uv run python script/project/data/scan.py .

s-project-proposal-new SLUG TITLE:
    uv run python script/project/proposal/new.py . {{SLUG}} {{TITLE}}

s-project-proposal-check SLUG:
    uv run python script/project/proposal/check.py . {{SLUG}}

s-project-proposal-approve SLUG ROLE TEXT:
    uv run python script/project/proposal/approve.py . {{SLUG}} {{ROLE}} {{TEXT}}

s-project-stage-new SLUG STAGE TITLE:
    uv run python script/project/stage/new.py . {{SLUG}} {{STAGE}} {{TITLE}}

s-project-experiment-new SLUG STAGE EXPERIMENT TITLE:
    uv run python script/project/experiment/new.py . {{SLUG}} {{STAGE}} {{EXPERIMENT}} {{TITLE}}

s-project-experiment-claim SLUG EXPERIMENT ROLE SESSION:
    uv run python script/project/experiment/claim.py . {{SLUG}} {{EXPERIMENT}} {{ROLE}} {{SESSION}}

s-project-experiment-release SLUG EXPERIMENT ROLE REASON:
    uv run python script/project/experiment/release.py . {{SLUG}} {{EXPERIMENT}} {{ROLE}} {{REASON}}

s-project-experiment-check:
    uv run python script/project/experiment/check.py .

s-project-result-submit SLUG EXPERIMENT RESULT ROLE SESSION TEXT:
    uv run python script/project/result/submit.py . {{SLUG}} {{EXPERIMENT}} {{RESULT}} {{ROLE}} {{SESSION}} {{TEXT}}

s-project-review-submit SLUG RESULT ROLE DECISION TEXT:
    uv run python script/project/review/submit.py . {{SLUG}} {{RESULT}} {{ROLE}} {{DECISION}} {{TEXT}}

s-project-question-ask SLUG ID ROLE TARGET_ROLE TARGET TEXT:
    uv run python script/project/question/ask.py . {{SLUG}} {{ID}} {{ROLE}} {{TARGET_ROLE}} {{TARGET}} {{TEXT}}

s-project-question-answer SLUG ID ROLE TEXT:
    uv run python script/project/question/answer.py . {{SLUG}} {{ID}} {{ROLE}} {{TEXT}}

s-project-question-check:
    uv run python script/project/question/check.py .

s-project-decision-submit SLUG ID ROLE TARGET_ROLE TARGET DECISION TEXT:
    uv run python script/project/decision/submit.py . {{SLUG}} {{ID}} {{ROLE}} {{TARGET_ROLE}} {{TARGET}} {{DECISION}} {{TEXT}}

s-project-decision-check:
    uv run python script/project/decision/check.py .

s-project-scan SLUG:
    uv run python script/project/scan.py . {{SLUG}}

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
