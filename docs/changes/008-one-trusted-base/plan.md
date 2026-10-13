# Plan: One trusted base branch

References: intent.md, spec.md, ux-brief.md

## Data shape
- Input: `cfg["base_branch"]` (from pod.yml) and `ci_base_ref()` (from the GitHub event, empty outside CI).
- `base_problem(cfg) -> str | None` is pure apart from reading the CI event. It holds the only copy of both rules (change branch, CI mismatch).
- `resolve_base(base, root)` takes the CI base first when there is one; otherwise it is unchanged.
- Callers: `pod_config_problems` (adds the problem); `peer_review` (refuses); `mode_record_on_base` and `plan_merged_as_is` (return None/False); the loop (refuses with the same text).

## Throughput checkpoint
- Blocking first steps: failing tests for R1 to R5 and E1, E2, E4, E5 in a new `tests/test_trusted_base.py`, then lock
- Independent workstreams: n/a: one helper and five call sites in scripts/lib.py and scripts/loop.py
- Shared mutable state: scripts/lib.py (`resolve_base`, `pod_config_problems`, `peer_review`, `mode_record_on_base`, `plan_merged_as_is`)
- Smallest safe decomposition: four steps, each ending with `make check`: (1) `base_problem` and `pod_config_problems`, (2) `resolve_base` in CI, (3) peer review and the mode record, (4) the loop and 007 switched to the helper

## Parallel parts
none: call sites in two files that must agree on one helper

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | `base_problem`; `resolve_base` prefers the CI base; `pod_config_problems`, `peer_review`, `mode_record_on_base`, `plan_merged_as_is` use it | R1–R6 |
| `scripts/loop.py` | the start check uses `lib.base_problem` | R6 |
| `tests/test_trusted_base.py` | new | R1–R5, E1, E2, E4, E5 |

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. Steps (1) to (4) above.

## Risks
- A pod whose PRs target another branch sees CI fail (spec flagged concern). The message names both branches.
- `resolve_base` is used by sponsor spend and agent-sign's diff. In CI they now read the PR's real base. Outside CI they are unchanged.

## Proof
- `make test` and `make strength` pass.
- R1 to R5 and the edge cases: the new test file. R6, R7: existing tests unchanged.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. A change can no longer point the base branch at itself to hide from agent-sign, peer review, budgets or mode records.
2. One place decides the base, so the next check that needs it is safe by default.
3. Risks: teams whose PRs target a branch other than `base_branch` will see CI say so.
