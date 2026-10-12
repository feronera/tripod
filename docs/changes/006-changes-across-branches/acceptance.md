# Acceptance: See changes on other branches

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| A third change is refused with two open changes on branches (`wip_limit: 2`), naming both | The reproduction from intent.md, in a fresh repository with this branch's kit | `Refused: 2 open changes reach the WIP limit (2)`, then `001-one (branch change/001-one)` and `002-two (branch change/002-two)`. Before: accepted, all numbered 001 | Yes |
| No number collides with a local or fetched remote branch | `NumberingTests`, `RemoteTests` | 001, 002, 003 from main; remote numbers skipped; a folder-less branch keeps its number | Yes |
| Merged or gate-4-complete changes do not count | `test_finished_change_does_not_count`, `test_local_branch_wins_over_remote` | Not counted | Yes |
| `make check` passes; existing tests unchanged | `make check` | 379 tests pass. No existing test file changed | Yes |

## Demo steps
1. In a fresh repository, start three changes from main, each on its own branch with gate 1 signed.
   - Expected: 001, 002, then refused.
   - Actual: as expected.
2. Run `new-change.sh` in this repository.
   - Expected: number 007, above the open 006 branch, in under 1 second.
   - Actual: 007 in 0.11 s. The probe folder was deleted.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: the WIP limit now works as the README and pod charter promise, and new changes no longer collide on numbers. Other commands are unchanged.
