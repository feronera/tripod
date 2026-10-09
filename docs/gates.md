# Gates

A pod has two roles, SuperBiz and SuperDev, each held by one or more people. Agents help draft the work of every role, but people make the decisions at 4 gates.
The principle "the author and the approver are different people" is kept by cross-gating: every gate needs the owner's approval and a cross-check from the other role.
Any member of a role may sign for that role (see `docs/scaling.md`).

| Gate | Artifact | Owner approves | Cross-check (cross) | Risk: high |
|---|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev (feasible and measurable?) | - |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev | + escalation |
| 3 | plan.md | SuperDev | SuperBiz (still matches the intent?) | - |
| 4 | PR / acceptance.md | SuperDev (code; with 2+ SuperDevs, one who did not write it) | SuperBiz (accepted against the Success measure) | + escalation |

## Gate 4 has two checks

| Check | Command | low | medium | high |
|---|---|---|---|---|
| merge-ready (can merge into main) | `scripts/gate-check.sh <dir> 4` | owner + cross, or a `role=auto` record | owner | owner + cross + escalation |
| release-ready (can release to production) | `scripts/release-check.sh <dir>` | owner + cross | owner + cross | owner + cross + escalation |

- Release-ready requires no stale approvals and no `event=revert` record.
- Auto-merge details and conditions are in `docs/merge-by-risk.md`.

## Gate 4 peer review (2 or more SuperDevs)

- The SuperDev who signs gate 4 as owner must not be the author of any code commit in the change.
  A code commit is a commit in `merge-base(HEAD, <base>)..HEAD` that touches a file outside `docs/`; its author is the commit author email.
  `<base>` is `origin/<base_branch>` when that ref exists, else `<base_branch>` (`base_branch` in pod.yml, default `main`).
- `scripts/gate.sh` refuses the signature, names the code authors and asks another SuperDev to sign.
  `scripts/pr-check.sh` checks the same rule on GitHub approvals in CI.
- When there is no merge base or no code commit (for example after the change has merged), the rule is skipped with a one-line note.
  `scripts/gate-check.sh` on `main` after a merge cannot evaluate it, so it does not try.
- When every SuperDev wrote code in the change, the rule falls back to the two-person rule: the SuperBiz cross-check is the second pair of eyes.
- With one SuperDev the rule does not apply: there is no other SuperDev to review, and the SuperBiz cross-check already separates writer and approver.

## How to sign

```bash
scripts/gate.sh docs/changes/001-slug 1     # the owner signs first, then the cross-checker
scripts/gate-check.sh docs/changes/001-slug  # check every gate recorded in gates.log
```

- Identity comes from `git config user.email`, and the role comes from `pod.yml`. An email listed in two roles cannot sign.
- Order: owner first, then cross, then escalation (when required).
  Exception: at gate 4, after a `role=auto` record, SuperBiz may sign cross first (acceptance after merge).
- Gate N can be signed only once gate N-1 is complete.
- Each line in `gates.log` stores the artifact's blob hash. If the artifact is edited after approval, the approval becomes stale and must be signed again.
- Agents never sign gates on behalf of people.

## Review questions for each gate

### Gate 1: intent.md
- Is the problem backed by real evidence, and are the users clearly identified?
- Is the Success measure a measurable number with a current value?
- Does the Risk section answer the 4 questions in `docs/risk-tiers.md`?
- (SuperDev) Does it fit in a single change, and can it be measured with the data available?

### Gate 2: spec.md and ux-brief.md
- Can every requirement (R1, R2, ...) be verified by a test or a demo?
- Do the edge cases cover empty data, invalid data and access permissions?
- Does the ux-brief cover all 4 states (empty, loading, error, success) and the user-facing copy?
- Has every Flagged concern been answered or accepted as a risk?
- (SuperDev) Is anything infeasible or more expensive than necessary?

### Gate 3: plan.md
- (Checked by script) `## Data shape` is filled in, `## Throughput checkpoint` has all 4 lines,
  and `## Parallel parts` is either `none: <reason>` or has at least 2 parts whose files do not overlap.
  If any is missing, `scripts/gate.sh` refuses to sign and `scripts/gate-check.sh` fails.
- Every requirement has files to change and a way to prove it (Proof).
- The order of work starts with failing tests.
- The Rollback is workable and lists its steps.
- (SuperBiz) Does the "Summary for SuperBiz" still match the intent?

### Gate 4: PR and acceptance.md
- (SuperDev) `make check` passes (including test strength), review.md has `blockers: 0`, and the tests were not edited after they were locked.
  With 2 or more SuperDevs, the signer did not write code in the change (review.md names the code authors).
- (SuperBiz) The demo result matches the Success measure, and acceptance.md states accept or reject with a reason.
- (Risk: high) Escalation has reviewed and signed.
