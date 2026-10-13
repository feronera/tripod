# Intent: Gate 4 reads its own artifacts

Status: draft

## Problem
Gate 4 can be signed, and a change reported ready to release, while its own review and acceptance say it is not ready.

Evidence:
- **Found on 2026-10-13** in a rehearsal of the pod deck with real Claude Code sessions on Tripod 1.0.6. The build stopped early, and `make check` failed. The review agent wrote `blockers: 1`, and the acceptance agent wrote `Decision: reject`.
- Even so, `scripts/gate.sh <dir> 4` recorded both signatures. `scripts/release-check.sh` printed `RELEASE-READY 001-order-history (Risk: medium)`.
- CI would still block the merge, because `make check` fails. But nothing stops a release from a change that its own acceptance rejected. auto-merge-check already refuses `blockers` above 0, so only the people's path lacks the check.

## Users
- People signing gate 4, and whoever releases a change.

## Success measure
- Gate 4 signatures accepted when review.md has `blockers` above 0, or acceptance.md has `Decision: reject`: from accepted to refused, with the reason.
- release-check on such a change: from `RELEASE-READY` to `NOT RELEASE-READY`, with the reason.
- `make check` passes; existing tests unchanged.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. People see a new refusal at gate 4.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**`, so it is high.

## Constraints
- Read only what the artifacts already state: the `blockers:` header of review.md, and the `Decision:` line of acceptance.md. No new fields.
- A missing review.md or acceptance.md keeps today's behavior.
- One parser for review.md: move `read_review` from merge_rules.py to lib.py rather than writing a second one.

## Open questions
- none
