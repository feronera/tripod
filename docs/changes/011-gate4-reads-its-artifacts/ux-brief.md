# UX brief: Gate 4 reads its own artifacts

References: intent.md

The users are people signing gate 4 or releasing, in a terminal.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/gate.sh <dir> 4` | Sign gate 4 | the refusal and its reasons | Fix the blockers, or change the acceptance decision |
| `scripts/release-check.sh <dir>` | Decide on a release | NOT RELEASE-READY with the reasons | Do not release |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| gate.sh 4 | As today | Not applicable | New refusal (copy below) | As today |
| release-check | As today | Not applicable | NOT RELEASE-READY with the new reasons | As today |

## Copy
| key | Text | Notes |
|---|---|---|
| refused | Refused: gate 4 cannot be signed while the change's own artifacts say it is not ready: | then `  - <reason>` lines |
| blockers | review.md has blockers: {N} | |
| reject | acceptance.md decides reject | |

## Accessibility notes
- Plain text, one reason per line.
