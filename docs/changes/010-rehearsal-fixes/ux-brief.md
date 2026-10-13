# UX brief: Fixes from the lab rehearsal

References: intent.md

The users are pod members signing gates in a terminal, and teams installing the kit.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/gate.sh <dir> <N>` | Sign a gate | `Recorded` lines, completion, and the next step | Commit and push gates.log |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| gate.sh | As today | Not applicable | New: the repeat-signature refusal | `Recorded …`, then `Next: share the signature: …` |

## Copy
| key | Text | Notes |
|---|---|---|
| next | Next: share the signature: git add {dir}/gates.log && git commit -m "gate {N}" && git push | After every recorded signature |
| repeat | Refused: you already signed gate {N} as {role} for the current {artifact}. The other role must be signed by someone else (see docs/gates.md) | stderr, exit 1 |

## Accessibility notes
- Plain text, one line each.
