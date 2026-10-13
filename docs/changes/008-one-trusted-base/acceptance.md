# Acceptance: One trusted base branch

References: intent.md, spec.md (amended)

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Checks redirectable by editing `base_branch` on the change's own branch: from 4 to 0 | one test per check in `tests/test_trusted_base.py`, failing before the code | agent-sign, peer review, the mode record (and spend, through agent-sign's refusal): all refused now | Yes |
| Per-function guards: from 2 to 1 shared place | code: the loop and 007 call `base_problem` | 1 | Yes |
| `make check` passes with existing tests unchanged | `make check`, also with the CI variables set | 409 tests pass; no existing test file changed | Yes |

## Demo steps
1. Set `base_branch: change/001-demo` and run `scripts/gate-check.sh --all`.
   - Expected: `FAIL pod.yml` with the change-branch message.
   - Actual: as expected (`ConfigTests`).
2. In CI (simulated), set `base_branch: develop` on a PR into main.
   - Expected: the mismatch message.
   - Actual: as expected (`BaseProblemTests`).

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: a change can no longer hide from agent-sign, peer review, budgets or the mode record by pointing the base at itself. The one remaining local case is caught in CI, by the PO's decision.
