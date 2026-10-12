# Spec: Signed plans stay valid after a kit upgrade

References: intent.md, ux-brief.md

## Requirements
- R1: When gate-check checks gate 3, it must skip the plan.md structure check (`check_plan`) if every role gate 3 requires has a latest signature whose `blob` equals the current plan.md. (verified by: test)
- R2: In every other case, including no signature, only some roles signed, or any required role's latest signature stale, gate-check must run the structure check and report its problems as today. (verified by: test, and the existing `PlanCheckTests` unchanged)
- R3: `scripts/gate.sh <dir> 3` must still refuse to sign a plan that fails the structure check, whatever is already signed. (verified by: test)
- R4: Every other gate-check rule is unchanged for a signed gate 3: roles, staleness, signing order, agent signatures and risk. (verified by: `make check` with existing tests unchanged)
- R5: docs/adopt.md, "Update the kit from upstream", gets one line: after the update, run `gate-check --all`; if it refuses one person in two roles, set `bootstrap: on` ([scaling.md](../../scaling.md)) or fix pod.yml. (verified by: review)

## Edge cases
- E1: A finished change whose plan fails a rule added later, with gates 1 to 4 signed: gate-check passes. This is the tripod-example change 003 case.
- E2: Gate 3 signed by the owner only, then the kit adds a rule: the cross-check must fail with the structure problem. gate.sh refuses the cross signature, and the plan must be fixed and signed again.
- E3: An agent signature at gate 3 (Autonomous mode) counts like a person's for R1. Its own checks (seat, model, usage) still run under R4.
- E4: The plan was edited after signing (stale): the structure check runs (R2) alongside the stale-approval problem.

## Flagged concerns
- This relaxes a check on signed work. The defense is that a signature with a matching blob means people approved exactly this text under the rules of its time, and gate.sh enforces the rules for every new signature.

## Out of scope
- Grandfathering other kinds of check (pod.yml config, risk paths). Only the plan structure is affected by format rules added after signing.
- Recording which kit version a change was signed under.
