# Acceptance: Simpler kit code

References: intent.md, spec.md (amended)

## Success measure check
| Success measure (intent) | How measured | Result | Pass? |
|---|---|---|---|
| scripts/*.py from 4,478 to 4,350 lines or fewer, with no behavior change except `--base` | `wc -l scripts/*.py` | 4,447 (−31). Behavior unchanged except `--base` | **No.** The line target was set from an estimate that was too high. Spec R10 was amended to the measured result with the PO's decision |
| One place that runs git, from 3 wrappers and about 14 raw calls | `grep 'subprocess.run(\["git"' scripts/` | 1 (`lib.git_out`) | Yes |
| Reading a file at a ref: from 6 places to 1; deciding the trusted base: from 6 to 1 | grep | 1 and 1 | Yes |
| `make check` passes; existing tests unchanged except the version assertion | `make check` | 412 tests pass; only `test_pod_v3`'s two version strings changed (approved) | Yes |

## Demo steps
1. Set `base_branch: trunk` with no `main` branch, then run `scripts/auto-merge-check.sh <dir>` with no `--base`.
   - Expected: ALLOW.
   - Actual: ALLOW. Before the change: "cannot compare with base 'main'".
2. Read the merge skill.
   - Expected: no `--base origin/main` and no manual risk-path step.
   - Actual: as expected.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: each small job now has one home, and the `--base` bug is fixed. The line-count goal was missed and is reported as missed.
