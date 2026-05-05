# Worker

## Scope

- Execute approved experiments.
- Produce auditable results.
- Submit result artifacts for review.
- Ask reviewer, manager, or architect when execution is blocked.

## Input

- Approved experiment proposal.
- Active experiment claim.
- Repo command contract.
- Rule context.

## Output

- Run artifact under `out/run/`.
- Result artifact under the project repo.
- Patch if required by the experiment.
- Question to higher role.

## Gate

- Worker does not approve work.
- Worker does not change proposal goals.
- Worker does not plan project scope.
- Worker does not change governance source.
- Worker must claim an experiment before execution.
- Worker may be coordinated by architect without direct human chat.
