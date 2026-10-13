# Spec: Fixes from the lab rehearsal

References: intent.md, ux-brief.md

## Requirements
- R1: After recording a signature, `scripts/gate.sh` must print one line: `Next: share the signature: git add <dir>/gates.log && git commit -m "gate <N>" && git push`. `<dir>` is the change folder as given. The line comes after the `Recorded` lines and the completion lines. (verified by: test)
- R2: `scripts/gate.sh` must refuse, before writing anything, when the latest gates.log entry for this gate, role and person already has the current artifact's blob. The message: `Refused: you already signed gate <N> as <role> for the current <artifact>. The other role must be signed by someone else (see docs/gates.md)`. Signing again after the artifact changed (a stale signature) is still allowed. (verified by: test)
- R3: The installer must add `__pycache__/` to `.gitignore`, with the kit's other lines, once. (verified by: test)
- R4: Existing tests pass unchanged. (verified by: `make check`)

## Edge cases
- E1: Bootstrap: the person who also holds escalation signs owner and escalation in one step, as today. R2 does not refuse that step.
- E2: An agent signature (`agent-sign.sh`) does not go through `gate.sh`, so R1 and R2 do not apply to it.
- E3: An existing `.gitignore` that already has `__pycache__/` is not changed.

## Flagged concerns
- none

## Out of scope
- `gate.sh` running git itself (intent constraint).
- Deck changes: a separate pull request in the workshop repository.
