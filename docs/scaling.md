# Growing the pod

A pod starts with one SuperBiz and one SuperDev. It can grow by giving a role more than one person. This page covers what changes when it does, where the work starts to queue, and when to split into two pods instead.

## More than one person per role

Every role key in `pod.yml` accepts a comma-separated list. The name, email and GitHub lists are aligned by position:

```yaml
superbiz_name: Bee
superbiz_email: bee@pod.example
superbiz_github: bee-gh
superdev_name: Dan, Eve
superdev_email: dan@pod.example, eve@pod.example
superdev_github: dan-gh, eve-gh
escalation_name: Lee
escalation_email: lee@pod.example
escalation_github: lee-gh
```

- A single value works exactly as before.
- Any member of a role acts for that role. Any SuperDev can sign gates 3 and 4 as owner and gates 1 and 2 as cross; any SuperBiz likewise.
- One person holds one role. `scripts/gate-check.sh --all` (and so `make check` and CI) fails when an email or GitHub login appears in two roles, or when a role's lists have different lengths. A role's `_github` list may be left out.
- `.github/CODEOWNERS` lists every SuperDev and escalation login for each risk path. Run `scripts/sync-codeowners.sh` after changing `pod.yml`.

![Pod of three: one SuperBiz and two SuperDevs build parallel parts; the gate 4 owner is the SuperDev who did not write the code](images/setup-3.svg)

## Peer review at gate 4

With two or more SuperDevs, the person who wrote the code should not be the one who approves it. So:

- The SuperDev who signs gate 4 as owner must not be the author of any code commit in the change. A code commit is a commit between the merge base with `origin/<base_branch>` (or `<base_branch>`) and HEAD that touches a file outside `docs/`. `base_branch` is set in `pod.yml` (default `main`).
- `scripts/gate.sh` refuses the signature and names the code authors and the SuperDevs who may sign instead. When there is no merge base or no code commit (for example after the change has merged), the rule is skipped with a one-line note.
- `scripts/pr-check.sh` checks the same rule on GitHub approvals in CI: for low (without a valid auto record), medium and high risk, the SuperDev approval must come from a SuperDev who neither opened the PR nor wrote code in it.
- If every SuperDev wrote code in the change, the rule falls back to the two-person rule: SuperBiz's cross-check is the second pair of eyes, as in a one-SuperDev pod. Keep one SuperDev as the reviewer when you can.
- With one SuperDev the rule does not apply: there is nobody else to review, and the SuperBiz cross-check already separates writer and approver.
- Low-risk auto-merge is unchanged. It relies on the agent reviewers, the second-model opinion and CI, not on a human peer (see `docs/merge-by-risk.md`).

## SuperBiz is the bottleneck

![Many pods install the same versioned kit, share an escalation for high-risk work, and feed lessons back into the kit](images/setup-n.svg)

SuperBiz owns gates 1 and 2 and cross-checks gates 3 and 4, so every change passes through SuperBiz four times. Adding SuperDevs without adding SuperBiz moves the queue to SuperBiz.

- Guideline: no more than 3 SuperDevs per SuperBiz. Above that, `gate-check --all` prints a warning (the exit code is not affected).
- Add a second SuperBiz before a fourth SuperDev.

## WIP limit

`wip_limit` stays pod-wide. A sensible starting point is 2 per SuperDev, capped by how many open changes SuperBiz can review at once. If changes often wait at gate 3 or 4 for SuperBiz, lower it.

## Parallel parts across SuperDevs

A part in `## Parallel parts` of plan.md may name its owner:

```markdown
### A
files: app/history.py
tests: tests/test_history.py
owner: dan@pod.example
```

- Gate 3 checks that every listed owner is a SuperDev in `pod.yml`. `scripts/parallel-check.sh` prints each part's owner next to its result.
- Each SuperDev builds their part in their own clone or worktree. Merge the parts in the order `parallel-check --run` reports.
- The gate 4 owner must be a SuperDev who did not write code in the change. If both SuperDevs of a two-SuperDev pod built parts, peer review falls back as described above, so keep one SuperDev as the reviewer when possible.

## When to split into two pods

Split when you see any of these:

- SuperBiz cross-checks regularly wait more than a day.
- WIP is always at the limit, and changes wait at the gates rather than in the build.
- The work covers unrelated product areas that need different business decisions.

Tripod reads one `pod.yml` per repository, so each pod works in its own repository with its own members, WIP limit and `docs/changes/`.

## SuperCEO

The `escalation` role can be a list too, so a high-risk approval can come from any of several leads. SuperCEO, a role for direction, priorities and high-risk approvals, remains planned; escalation stands in for it today.
