# Acceptance: Signed plans stay valid after a kit upgrade

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Finished changes that fail a newer plan rule after an upgrade: from failing to passing | tripod-example upgraded from 0.5.x with this branch's kit, `scripts/gate-check.sh --all` | 003-order-page: before, `FAIL` (parts A and B have no `tests:` line); after, `OK (passed up to gate 4 merge-ready)` | Yes |
| Unsigned or stale plans are still checked as today | existing `PlanCheckTests` unchanged; new tests for branch-only, partial, edited and hand-signed plans | all pass | Yes |

## Demo steps
1. Upgrade tripod-example (branch `change/004-kit-1-0-2`, local) with `pod-install.sh --vendor-plugins --force`. Keep pod.yml and add `bootstrap: on`.
   - Expected: `gate-check --all` passes 001, 002 and 003.
   - Actual: as expected.
2. On a branch whose pod.yml names itself as `base_branch`, with a hand-signed old-format plan.
   - Expected: the plan rule still fails.
   - Actual: as expected (`BaseRedirectTests`).

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: upgrades no longer turn merged changes red, and nothing on a branch skips the plan check.

Next: release 1.0.3, then open the tripod-example upgrade through its own gates.
