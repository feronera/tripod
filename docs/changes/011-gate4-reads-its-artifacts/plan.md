# Plan: Gate 4 reads its own artifacts

References: intent.md, spec.md, ux-brief.md

## Data shape
- review.md header: `{blockers, majors_open, second_opinion, reviewed_head}` from `read_review`, moved to lib.py.
- acceptance.md: the first line matching `Decision: <word>`.
- `not_ready(change_dir) -> [reasons]`.

## Throughput checkpoint
- Blocking first steps: failing tests for R1 to R3 and E1 to E3 in a new `tests/test_gate4_artifacts.py`, then lock
- Independent workstreams: n/a: one helper and two call sites in scripts/lib.py, one import change in scripts/merge_rules.py
- Shared mutable state: scripts/lib.py (`cmd_gate`, `release_problems`)
- Smallest safe decomposition: two commits, each ending with `make check`: (1) move `read_review` (R4), (2) `not_ready` and its two call sites (R1 to R3)

## Parallel parts
none: one helper and two call sites

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | `read_review` (moved), `not_ready`, used in `cmd_gate` for gate 4 and in `release_problems` | R1–R4 |
| `scripts/merge_rules.py` | uses `lib.read_review` | R4 |
| `tests/test_gate4_artifacts.py` | new | R1–R3, E1–E3 |

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. Steps (1) and (2).
3. Re-run the real Claude Code rehearsal's Labs 6 and 7, with git commit allowed.

## Risks
- An existing test signs gate 4 with a review.md that has blockers, or an acceptance that rejects. `make check` after step (2) shows it.

## Proof
- `make test` and `make strength` pass. R1 to R3, E1 to E3: the new test file. R4, R5: existing tests.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. Gate 4 cannot be signed while the review has blockers or the acceptance says reject.
2. release-check says NOT RELEASE-READY in the same cases.
3. Risks: none for changes that are ready.
