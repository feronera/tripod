# Spec: Signed plans stay valid after a kit upgrade

References: intent.md, ux-brief.md

Amended on 2026-10-13 after gate 3, before any code. The existing test `PlanCheckTests.assert_refused` requires that gate-check still fails a signature written into gates.log by hand on a bad plan, a defense against bypassing gate.sh. Skipping the check for any signed plan would remove that defense. R1 now trusts only a plan already on the base branch, as `mode_record_on_base` does for Autonomous-mode records: it got there through CI.

## Requirements
- R1: When gate-check checks gate 3, it must skip the plan.md structure check (`check_plan`) only when the base branch (`base_branch`, resolved as today) already holds this change's plan.md with the same blob as the working tree, and the base branch's gates.log has, for every role gate 3 requires, a latest gate 3 signature with that blob. (verified by: test)
- R2: In every other case, including signatures that exist only on a branch or in the working tree, partial signatures, or a plan that differs from the base branch, gate-check must run the structure check and report its problems as today. (verified by: test, and the existing `PlanCheckTests` unchanged, including the hand-signed case)
- R3: `scripts/gate.sh <dir> 3` must still refuse to sign a plan that fails the structure check, whatever is already signed. (verified by: test)
- R4: Every other gate-check rule is unchanged for a signed gate 3: roles, staleness, signing order, agent signatures and risk. (verified by: `make check` with existing tests unchanged)
- R5: docs/adopt.md, "Update the kit from upstream", gets one line: after the update, run `gate-check --all`; if it refuses one person in two roles, set `bootstrap: on` ([scaling.md](../../scaling.md)) or fix pod.yml. (verified by: review)

## Edge cases
- E1: A finished, merged change whose plan fails a rule added later: gate-check passes on the base branch and on any branch made from it. This is the tripod-example change 003 case.
- E5: Not a git repository, or no base branch: no skip, the structure check runs as today.
- E2: Gate 3 signed by the owner only, then the kit adds a rule: the cross-check must fail with the structure problem. gate.sh refuses the cross signature, and the plan must be fixed and signed again.
- E3: An agent signature at gate 3 (Autonomous mode) counts like a person's for R1. Its own checks (seat, model, usage) still run under R4.
- E4: The plan was edited after signing (stale): the structure check runs (R2) alongside the stale-approval problem.

## Flagged concerns
- This relaxes a check on merged work only. A plan and its signatures on the base branch passed CI (`make check`) when they merged, under the rules of that time. gate.sh enforces the current rules for every new signature, and anything on a branch is still checked.

## Out of scope
- Grandfathering other kinds of check (pod.yml config, risk paths). Only the plan structure is affected by format rules added after signing.
- Recording which kit version a change was signed under.
