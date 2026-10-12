# Plan: Signed plans stay valid after a kit upgrade

References: intent.md, spec.md, ux-brief.md

## Data shape
- Input: the gate 3 entries of gates.log, the roles gate 3 requires (`required_roles(3, risk)`), and the current `blob_hash(plan.md)`.
- One helper: `plan_merged_as_is(change_dir, cfg, roles, blob)`. It reads plan.md and gates.log from the base branch with `git show` (as `mode_record_on_base` does), and returns True when the base plan.md has `blob` and, for each role, the latest base gate 3 entry has `blob`.
- `check_gate` runs `check_plan` only when `not plan_merged_as_is(...)`. `cmd_gate` keeps its own `check_plan` call before signing, so R3 needs no code.

## Throughput checkpoint
- Blocking first steps: failing tests for R1, R2, R3, E1, E2 and E4 in a new `tests/test_signed_plans.py`, then lock
- Independent workstreams: n/a: one helper and one call site in scripts/lib.py, plus one line in docs/adopt.md
- Shared mutable state: scripts/lib.py (`check_gate`)
- Smallest safe decomposition: three steps, each ending with `make check`: (1) the helper and the call site, (2) the adopt.md line, (3) repeat the tripod-example upgrade with this branch's kit

## Parallel parts
none: one call site in one file

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | `plan_merged_as_is`; `check_gate` skips `check_plan` for gate 3 when it returns True | R1, R2, R4 |
| `docs/adopt.md` | one line in step 9 | R5 |
| `tests/test_signed_plans.py` | new: a plan signed under the old format passes; partial, stale and new signatures still checked; gate.sh still refuses | R1–R3, E1, E2, E4 |

The tests make an "old-format" plan (a Parallel part without `tests:`) with gates.log entries for its blob, as an older kit would have accepted. They commit it to `main` (merged) or leave it on a branch or uncommitted (not merged). This mirrors an upgrade without needing two kit versions.

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. Steps (1) to (3) above.

## Risks
- A plan edited after merging differs from the base blob, so R2 checks it. Signature lines forged on a branch are not on the base branch, so they are checked too.
- E3 (agent signatures) is covered because `plan_merged_as_is` reads the same entries on the base branch; agent checks still run in the role loop.

## Proof
- `make test` and `make strength` pass.
- R1 to R3 and E1, E2, E4: the new test file.
- Success measure: tripod-example change 003 passes `gate-check --all` with this branch's kit (acceptance.md).

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. Upgrading the kit no longer turns finished changes red when a newer plan rule appears.
2. New and re-signed plans are checked exactly as before.
3. Risks: only merged plans are trusted, because they passed CI when they merged. Anything on a branch is checked as today.
