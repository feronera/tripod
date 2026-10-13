# Acceptance: Gate 4 reads its own artifacts

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Gate 4 signatures when review.md has blockers or acceptance.md rejects: from accepted to refused | tests; real Claude Code rehearsal | refused, with the reasons | Yes |
| release-check on such a change: from RELEASE-READY to NOT RELEASE-READY | tests; rehearsal | NOT RELEASE-READY, with the reasons | Yes |
| `make check` passes; existing tests unchanged | `make check` | 424 pass; no existing test changed | Yes |

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: people can no longer sign or release a change that its own review or acceptance says is not ready, and changes that are ready are unaffected.
