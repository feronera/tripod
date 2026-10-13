# Plan: Simpler kit code

References: intent.md, spec.md, ux-brief.md

## Data shape
- `lib.git(args, root, text=True, strip=True, quotepath=True) -> (rc, out, err)`: the only place that runs git. `git_out` stays as its current name for existing callers, or is renamed with all callers in one step.
- `lib.show(ref, path, root) -> bytes | None`: `git show ref:path`.
- `lib.trusted_base(cfg, root) -> (ref | None, problem | None)`: `(None, problem)` when `base_problem` refuses, else `(resolve_base(...), None)`.
- `lib.parse_risk_paths(text) -> [globs]`, with `read_risk_paths` reading the file and calling it.

## Throughput checkpoint
- Blocking first steps: failing tests for R7 and E2 (auto-merge-check's default base) in a new `tests/test_simpler_kit.py`, then lock
- Independent workstreams: n/a: small edits across lib.py, merge_rules.py, loop.py, sponsor.py, superceo.py, activity.py, pod_install.py and three text files, which must agree on four helpers
- Shared mutable state: scripts/lib.py (the four helpers)
- Smallest safe decomposition: one commit per item, each ending with `make check`: (1) R1, (2) R2, (3) R3, (4) R4, (5) R5, (6) R6, (7) R7, (8) R8 and R9

## Parallel parts
none: every step depends on the helpers in lib.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | dead code out; `git`, `show`, `trusted_base`, `parse_risk_paths`; callers use them | R1–R5 |
| `scripts/merge_rules.py`, `scripts/loop.py`, `scripts/sponsor.py`, `scripts/superceo.py`, `scripts/activity.py`, `scripts/agent_sign.py`, `scripts/pod_install.py` | use the helpers; `--base` default | R2–R7 |
| `AGENTS.md`, `plugins/superdev/hooks/gate-guard.sh` (comment only), `plugins/superdev/skills/merge/SKILL.md` | point to docs/merge-by-risk.md | R8 |
| `plugins/*/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | 1.0.1 | R9 |
| `tests/test_pod_v3.py` | the version assertion 1.0.0 to 1.0.1 (PO approval) | R9 |
| `tests/test_simpler_kit.py` | new | R7, E2 |

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. Steps (1) to (8) above.

## Risks
- A refactor changes behavior unnoticed. Mitigation: one item per commit, and the existing 409 tests after each.
- `merge_rules.git` keeps trailing newlines today. Callers already strip or split, which is checked per call site in step (2).

## Proof
- `make test`, `make strength` and `claude plugin validate --strict` pass.
- R7, E2: the new test file. R1 to R6: grep and the existing tests. R10: `wc -l`.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. The kit's scripts do each small job in one place, so the next fix lands everywhere at once.
2. Auto-merge compares against your real base branch by default, and agents follow a shorter merge skill.
3. Risks: a refactor could slip. Every step is checked by the full test suite.
