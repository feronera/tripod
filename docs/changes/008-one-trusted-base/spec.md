# Spec: One trusted base branch

References: intent.md, ux-brief.md

The open question is decided: a refused base is reported as a pod.yml problem. Every check that grants trust (agent-sign, peer review, the mode record, the plan skip) then refuses or treats the base as unknown. A fallback to `main` would guess wrong in repositories whose base is another branch.

## Requirements
- R1: `lib.base_problem(cfg)` must return a problem, or None:
  - when `base_branch`, without an `origin/` prefix, starts with `change/`: `base_branch: <name> is a change branch; the base must be the shared branch changes merge into (pod.yml base_branch, default main)`. This is the loop's current text.
  - in CI, when the pull request's base (`ci_base_ref`, from change 007) is known and differs from `base_branch`: `base_branch: <name> does not match the pull request's base branch <ci>`.

  (verified by: test)
- R2: `pod_config_problems` must include R1's problem. So `gate-check --all` and CI fail, and `agent-sign.sh` refuses before starting an agent, which also covers its diff and the sponsor's spend. (verified by: test)
- R3: In CI, `resolve_base` must use the pull request's base and ignore pod.yml. Outside CI it is unchanged: `origin/<base_branch>` when that ref exists, else `<base_branch>`. (verified by: test)
- R4: `scripts/gate.sh <dir> 4` must refuse the gate 4 owner signature with R1's problem when the pod has two or more SuperDevs and `base_problem` is not None, instead of skipping peer review. (verified by: test)
- R5: `mode_record_on_base` must return None when `base_problem` is not None, so an `event=mode` record never counts through a redirected base. (verified by: test)
- R6: `plan_merged_as_is` (007) and the loop's start check must use `base_problem` instead of their own guards. The existing tests for both pass unchanged. (verified by: `make check`)
- R7: Existing tests pass unchanged. (verified by: `make check`)

## Edge cases
- E1: Running locally on main with `base_branch: main`: no problem (the base may be the current branch).
- E2: `base_branch: origin/change/x`: refused, like `change/x`.
- E3: CI on a `pull_request_review` event: the base comes from the event payload, as in 007.
- E4: CI on a push (no pull request): `ci_base_ref` is empty, so pod.yml is used, as today.
- E5: A pod with one SuperDev: peer review does not apply, so R4 does not refuse. R2 still fails `gate-check --all`.

## Flagged concerns
- A team whose pull requests target a branch other than `base_branch` will now see CI fail with R1's mismatch message. That is intended: every gate check compares against `base_branch`, so it must be the branch the pull request merges into.

## Out of scope
- Protecting the base branch itself, which is `scripts/setup-github.sh`'s job.
- Running locally with forged local refs. Whoever controls the machine can already edit any file.
