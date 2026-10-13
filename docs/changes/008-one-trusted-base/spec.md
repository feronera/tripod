# Spec: One trusted base branch

References: intent.md, ux-brief.md

The open question is decided: a refused base is reported as a pod.yml problem. Every check that grants trust (agent-sign, peer review, the mode record, the plan skip) then refuses or treats the base as unknown. A fallback to `main` would guess wrong in repositories whose base is another branch.

Amended on 2026-10-13 after the second opinion, with the PO's decision. Outside CI, R1 now normalizes the name, so spelling variants of a change branch are refused too. A branch an attacker creates at HEAD under another name cannot be told apart from a branch freshly made from main, so outside CI it is out of scope; CI refuses it (R1 mismatch). This narrows intent.md's constraint "the branch currently checked out is refused": a base equal to the current branch is normal on main (E1).

## Requirements
- R1: `lib.base_problem(cfg)` must return a problem, or None. It first strips `refs/heads/`, `refs/remotes/origin/`, `heads/`, `remotes/origin/`, `origin/` and `./` from `base_branch`.
  - when the rest is not a plain branch name (only letters, digits, `.`, `_`, `-` and `/`; not `HEAD` or `@`; no `..`; not starting with `-` or `/`): `base_branch: <name> is not a plain branch name`.
  - when the rest starts with `change/`, in any letter case: `base_branch: <name> is a change branch; the base must be the shared branch changes merge into (pod.yml base_branch, default main)`. This is the loop's current text.
  - in CI, when the pull request's base (`ci_base_ref`, from change 007) is known and differs from the stripped name: `base_branch: <name> does not match the pull request's base branch <ci>`.

  (verified by: test)
- R2: `pod_config_problems` must include R1's problem. So `gate-check --all` and CI fail, and `agent-sign.sh` refuses before starting an agent, which also covers its diff and the sponsor's spend. (verified by: test)
- R3: In CI, `resolve_base` must use the pull request's base and ignore pod.yml. Outside CI it is unchanged: `origin/<base_branch>` when that ref exists, else `<base_branch>`. (verified by: test)
- R4: `scripts/gate.sh <dir> 4` must refuse the gate 4 owner signature with R1's problem when the pod has two or more SuperDevs and `base_problem` is not None, instead of skipping peer review. (verified by: test)
- R5: `mode_record_on_base` must return None when `base_problem` is not None, so an `event=mode` record never counts through a redirected base. (verified by: test)
- R6: `plan_merged_as_is` (007) and the loop's start check must use `base_problem` instead of their own guards. The existing tests for both pass unchanged. (verified by: `make check`)
- R7: Existing tests pass unchanged, in CI too. `tests/__init__.py` clears `GITHUB_EVENT_PATH` and `GITHUB_BASE_REF`, so the kit's own tests always run as outside CI, whatever pull request CI is checking. Tests that need CI set the variables themselves. (verified by: `make check`, and CI on this pull request)

## Edge cases
- E1: Running locally on main with `base_branch: main`: no problem (the base may be the current branch).
- E2: `base_branch: origin/change/x`, `refs/heads/change/x`, `heads/change/x`, `./change/x` or `Change/x`: refused, like `change/x`. `@` and `HEAD` are refused as not plain names.
- E3: CI on a `pull_request_review` event: the base comes from the event payload, as in 007.
- E4: CI on a push (no pull request): `ci_base_ref` is empty, so pod.yml is used, as today.
- E5: A pod with one SuperDev: peer review does not apply, so R4 does not refuse. R2 still fails `gate-check --all`.

## Flagged concerns
- A team whose pull requests target a branch other than `base_branch` will now see CI fail with R1's mismatch message. That is intended: every gate check compares against `base_branch`, so it must be the branch the pull request merges into.

## Out of scope
- Protecting the base branch itself, which is `scripts/setup-github.sh`'s job.
- Running locally with forged local refs. Whoever controls the machine can already edit any file.
- Outside CI, a base named like an ordinary branch that points at the change itself (for example `feature-x` created at HEAD). CI refuses it, because the name does not match the pull request's base. pr-check and auto-merge-check read the real base from the GitHub event and never from pod.yml.
