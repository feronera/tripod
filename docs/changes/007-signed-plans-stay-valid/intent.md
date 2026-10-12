# Intent: Signed plans stay valid after a kit upgrade

Status: draft

## Problem
`gate-check` runs the plan.md structure check every time it checks gate 3, including for changes whose gate 3 was signed long ago and that have already merged. When a kit release adds a structure rule, every finished change written before it fails, and `make check` (and so CI) goes red after the upgrade.

Evidence:
- **Found on 2026-10-13** while upgrading feronera/tripod-example from kit 0.5.x to 1.0.2.
- Its change 003 (order page) passed all four gates and merged on 2026-10-09. After the upgrade, `gate-check --all` fails it: "plan.md part `### A: page rendering` has no `tests:` line", and the same for part B. Gate 4 then fails with "requires gate 3 complete first".
- **No workaround exists.** Editing the old plan.md to satisfy the new rule makes every gate 3 signature stale, so the people would have to re-sign a change that is already in production.
- **Every team that upgrades** and has finished changes with Parallel parts written under an older format hits this.
- `scripts/gate.sh` already refuses to sign a plan that fails the structure check, so the rule is enforced at the moment it matters.

## Users
- Pods upgrading the kit (docs/adopt.md, "Update the kit from upstream").
- Their CI, which runs `make check` on every pull request.

## Success measure
- Finished changes that fail a newer plan rule after an upgrade: from failing to passing. Measured by repeating the tripod-example upgrade, where change 003 must pass `gate-check --all`.
- A plan that is not yet signed, or whose signature is stale, is still checked and refused exactly as today. Measured by the existing plan-structure tests, which must pass unchanged.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Every team's `gate-check` result changes for old signed plans.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**`, and it relaxes a gate check, so it is high.

## Constraints
- Only the plan.md structure check changes. Signatures, staleness, roles, risk and every other check stay as they are.
- Keep it small: skip the structure check only when every role gate 3 needs has signed the current plan.md. Do not add version tracking or a list of grandfathered rules.

## Open questions
- Should the other upgrade finding (one GitHub login in two roles needs `bootstrap: on`) also be handled here? Proposal: no. It is a correct refusal; the upgrade guide in docs/adopt.md gets one line telling teams to check `gate-check --all` and set `bootstrap: on` if one person holds two roles.
