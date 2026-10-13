# Acceptance: Fixes from the lab rehearsal

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| The kit says how to share every signature | rehearsal output | `Next: share the signature: …` after every signature | Yes |
| auto-merge-check's line count for the 9-line change in Lab 7: from 210 to 9 | rehearsal output | no line-limit reason; the two expected reasons only | Yes |
| A repeat signature is refused with a message | rehearsal Lab 3 and tests | `Refused: you already signed gate 1 as owner …` | Yes |
| `make check` passes; existing tests unchanged | `make check` | 418 pass; two installer assertions gain one line (approved) | Yes |

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: the three problems the rehearsal found in the kit are fixed, and the rehearsal passes without stand-ins for them. The deck's own fixes follow in the workshop repository.
