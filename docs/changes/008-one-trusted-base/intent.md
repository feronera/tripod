# Intent: One trusted base branch

Status: draft

## Problem
Six checks read the base branch from `base_branch` in pod.yml. A change can edit pod.yml on its own branch, so it can point the base at itself and hide from the checks that compare against the base.

Evidence:
- The second opinion on change 007 showed it by experiment for the plan check. With `base_branch: change/001-old` on that branch, a forged signature skipped the structure check. CI fetches every branch, so `origin/<the PR's own branch>` exists there too. Change 007 guarded only its own function.
- The same lookup (`resolve_base(cfg["base_branch"])`) is used by:

  | Check | What a redirected base hides |
  |---|---|
  | `agent_sign.changed_files` (Autonomous mode) | the branch's own diff: risky paths, governance files and forbidden paths, including the pod.yml edit itself |
  | gate 4 peer review (`code_authors`) | who wrote the code, so the peer rule falls back |
  | sponsor spend from the base branch | money already spent on main, so budgets look lower |
  | `mode_record_on_base` | it lets a forged `event=mode` record count |
  | the loop's `base_rules` | already refuses a `change/*` base |
  | `plan_merged_as_is` (007) | already guarded, in its own code |
- pod.yml is in docs/risk-paths, so a person reviews the edit. But the checks are there so that a missed review is not the only defense.

## Users
- Pods in Autonomous mode, whose sponsor relies on agent-sign and the budgets.
- Pods with two or more SuperDevs, who rely on peer review at gate 4.
- Every pod's CI.

## Success measure
- Checks that can be redirected by editing `base_branch` on a change's own branch: from 4 unguarded (agent-sign, peer review, spend, mode record) to 0. Measured by one test per check that sets `base_branch` to the change's own branch.
- Guards written per function: from 2 (loop, 007) to 1 shared place.
- `make check` passes with existing tests unchanged.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Teams whose pod.yml names an unusual base may see a new refusal.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**`, and it hardens gate checks, so it is high.

## Constraints
- One place decides the base. Every caller uses it, and the two existing guards are removed in its favor.
- In CI, the pull request's real base (from the GitHub event, as in 007) wins over pod.yml.
- Outside CI, a `change/*` base, or the branch currently checked out, is refused, and `gate-check --all` says so.
- No new pod.yml keys.

## Open questions
- Outside CI, what should a check do when the base is refused: fail closed, or fall back to `main`? Proposal: the check reports the problem and treats the base as unknown, which each caller already handles as "nothing on the base" (fail closed for trust, open for discovery). The spec will list each caller's result.
