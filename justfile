set shell := ["bash", "-lc"]

default:
    just --list

init:
    just venv && \
    just sync

venv:
    test -d .venv || uv venv

sync:
    uv sync --all-packages

sync-lock:
    uv sync --locked --all-packages

up:
    uv lock --upgrade

add PKG:
    uv add {{PKG}}

add-dev PKG:
    uv add --dev {{PKG}}

rm PKG:
    uv remove {{PKG}}

rm-dev PKG:
    uv remove --dev {{PKG}}

fmt:
    just sync && \
    uv run ruff format .

fmt-check:
    uv run ruff format --check .

lint:
    uv run ruff check . --fix

lint-check:
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
    just s-context-workflow-write
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

s-context-workflow-role-write:
    uv run python script/context/workflow/role/write.py . workflow/role context/workflow/role

s-context-workflow-mode-write:
    uv run python script/context/workflow/mode/write.py . workflow/mode context/workflow/mode

s-context-workflow-lifecycle-write:
    uv run python script/context/workflow/lifecycle/write.py . workflow/lifecycle context/workflow/lifecycle

s-context-workflow-artifact-write:
    uv run python script/context/workflow/artifact/write.py . workflow/artifact context/workflow/artifact

s-context-workflow-write:
    just s-context-workflow-role-write
    just s-context-workflow-mode-write
    just s-context-workflow-lifecycle-write
    just s-context-workflow-artifact-write
    just s-context-index-write

s-context-agent-write:
    uv run python script/context/agent/write.py . agent/doc context/agent

s-context-index-write:
    uv run python script/context/index/write.py . context

s-agent-change-new title worker:
    uv run python script/agent/change/new.py . out/agent/change out/agent/session "{{title}}" "{{worker}}"

s-agent-session-new role:
    uv run python script/agent/session/new.py . out/agent/session "{{role}}"

s-agent-change-review change reviewer status risk:
    uv run python script/agent/change/review.py . out/agent/change out/agent/session "{{change}}" "{{reviewer}}" "{{status}}" "{{risk}}"

s-agent-change-decide change decision:
    uv run python script/agent/change/decide.py . out/agent/change "{{change}}" "{{decision}}"

s-agent-change-commit change commit:
    uv run python script/agent/change/commit.py . out/agent/change "{{change}}" "{{commit}}"

s-agent-change-new-latest title:
    worker=`uv run python script/agent/query/latest.py . out/agent/session session worker`; uv run python script/agent/change/new.py . out/agent/change out/agent/session "{{title}}" "$worker"

s-agent-change-review-latest status risk:
    change=`uv run python script/agent/query/latest.py . out/agent/change change active`; reviewer=`uv run python script/agent/query/latest.py . out/agent/session session reviewer`; uv run python script/agent/change/review.py . out/agent/change out/agent/session "$change" "$reviewer" "{{status}}" "{{risk}}"

s-agent-change-approve-latest:
    uv run python script/agent/change/approve.py . out/agent/change config/agent.yaml latest

s-agent-session-retire session reason:
    uv run python script/agent/session/retire.py . out/agent/session "{{session}}" "{{reason}}"

s-agent-session-retire-latest role reason:
    session=`uv run python script/agent/query/latest.py . out/agent/session session "{{role}}"`; uv run python script/agent/session/retire.py . out/agent/session "$session" "{{reason}}"

s-agent-patch-check change:
    uv run python script/agent/patch/check.py . out/agent/change "{{change}}"

s-agent-patch-check-latest:
    change=`uv run python script/agent/query/latest.py . out/agent/change change active`; uv run python script/agent/patch/check.py . out/agent/change "$change"

s-agent-patch-apply change:
    uv run python script/agent/patch/apply.py . out/agent/change config/agent.yaml "{{change}}"

s-agent-patch-apply-latest:
    change=`uv run python script/agent/query/latest.py . out/agent/change change active`; uv run python script/agent/patch/apply.py . out/agent/change config/agent.yaml "$change"

s-agent-task-check-latest:
    change=`uv run python script/agent/query/latest.py . out/agent/change change active`; uv run python script/agent/change/check.py . out/agent/change "$change"

o-doctor:
    opencode --version

o-tui:
    opencode --pure

o-serve:
    opencode serve --pure --hostname 0.0.0.0 --port 4096

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
