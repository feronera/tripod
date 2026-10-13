blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: b9c4ec672be1659801155589985be0dff22eeeb4

# Review: One trusted base branch

## What changed
- `scripts/lib.py`:
  - `base_problem` is the only place that decides whether `base_branch` can be trusted. It normalizes the name (`refs/heads/`, `heads/`, `origin/`, `remotes/origin/`, `./`). It refuses names that are not plain branch names, and change branches in any spelling. In CI it also refuses a name that differs from the pull request's base.
  - `pod_config_problems` adds the problem, so `gate-check --all`, CI and `agent-sign.sh` refuse.
  - `resolve_base` prefers the pull request's base in CI.
  - Peer review at gate 4 refuses instead of skipping. `mode_record_on_base` and `plan_merged_as_is` (007) treat the base as unknown.
- `scripts/loop.py`: the start check uses `base_problem`. Its message text is unchanged.
- `tests/__init__.py`: the kit's own tests run as outside CI.

## Evidence that the bypasses were real
The first tests (8c19435) failed before the code. With `base_branch` set to the change's own branch:
- agent-sign started an agent;
- a forged `event=mode` record counted ("OK 001-demo (passed up to gate 2)");
- the code author signed gate 4 without peer review.

All three are refused now.

## Second opinion (Sonnet 5.5, independent)
- blockers_found 0. The CI path was found sound:
  - pr-check and auto-merge-check read the base from the GitHub event, never from pod.yml;
  - uncommitted pod.yml edits are seen by agent-sign;
  - normal pods pass on pull_request, pull_request_review and push.
- Verdict: agree after the Major below.

| Finding | Severity | Outcome |
|---|---|---|
| Outside CI only the literal `change/` prefix was refused. `refs/heads/change/x`, `heads/`, `./`, `Change/x`, `@` and a branch made at HEAD (`feature-x`) still redirected | Major | Fixed for every spelling and for odd names (`VariantTests`). The PO decided that a branch made at HEAD under an ordinary name is out of scope outside CI, where it cannot be told apart from a fresh branch from main. CI refuses it. Spec amended, gates 2 and 3 signed again |
| `refs/heads/main` in pod.yml failed the CI match | Minor | Fixed: the match uses the normalized name |
| In CI the kit's own tests would see the real PR's base | Minor | Fixed: `tests/__init__.py` clears the variables (`IsolationTests`). `make check` with the CI variables set passes |

## Test edits (PO approved on 2026-10-13)
- `tests/test_trusted_base.py` was locked at 8c19435 and is unchanged.
- `tests/test_trusted_base_review.py` is new (56ca6cc).
- `tests/__init__.py` was empty and now clears two variables (plan R7).

## Checks
- `make check`: pass, 409 tests, both normally and with `GITHUB_BASE_REF` and `GITHUB_EVENT_PATH` set as in CI.

## Open (not in this change)
- A branch numbered 999 still makes the next number 1000 (from change 006).

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
