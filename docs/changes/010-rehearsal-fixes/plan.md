# Plan: Fixes from the lab rehearsal

References: intent.md, spec.md, ux-brief.md

## Data shape
- gates.log entries as today. R2 looks for the latest entry with the same `gate`, `role` and `by`, and compares its `blob` with the current artifact's blob.

## Throughput checkpoint
- Blocking first steps: failing tests for R1, R2, R3, E1 and E3 in a new `tests/test_rehearsal_fixes.py`, then lock
- Independent workstreams: n/a: two small edits in scripts/lib.py (`cmd_gate`) and one in scripts/pod_install.py
- Shared mutable state: scripts/lib.py `cmd_gate`
- Smallest safe decomposition: three commits (R1, R2, R3), each ending with `make check`, then the rehearsal script without the stand-ins

## Parallel parts
none: three small edits

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | `cmd_gate`: the repeat refusal and the next-step line | R1, R2 |
| `scripts/pod_install.py` | `GITIGNORE_LINES` gains `__pycache__/` | R3 |
| `tests/test_rehearsal_fixes.py` | new | R1–R3, E1, E3 |

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. R1, R2 and R3, each ending with `make check`.
3. Run the rehearsal script without its stand-in steps.

## Risks
- An existing test signs the same gate twice on purpose. Mitigation: `make check` after R2. Any such test would show the behavior was relied on, and the PO decides.

## Proof
- `make test` and `make strength` pass.
- R1 to R3: the new test file. The success measure: the rehearsal run, recorded in acceptance.md.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. After signing, the kit says how to share the signature, so the other person can sign next.
2. Python's compiled files are no longer committed, so auto-merge counts the real change.
3. Signing the same gate twice is refused with a clear reason.
