# Merge by risk

Gate 4 is split into two checks:
- **merge-ready** (`scripts/gate-check.sh <change-dir> 4`): can the change merge into main? The gate-guard hook and CI use this check.
- **release-ready** (`scripts/release-check.sh <change-dir>`): can the change be released to production?

## Who does what at each tier

| Effective risk | merge-ready | Who merges | GitHub approval (pr-check) | release-ready |
|---|---|---|---|---|
| low | owner + cross, or a `role=auto` record | an agent, when `auto-merge-check` prints ALLOW | none when the auto record passes auto-merge-check again in CI; otherwise SuperDev | owner + cross (SuperBiz accepts within `acceptance_hours`) |
| medium | owner (SuperDev) | SuperDev, or an agent after SuperDev signs | SuperDev | owner + cross |
| high | owner + cross + escalation | a human | SuperDev, SuperBiz and escalation | owner + cross + escalation |

- Effective risk is the Risk in intent.md, except that a diff touching any path in `docs/risk-paths` is always high.
- The GitHub approver must not be the PR author. If the agent opens PRs with SuperDev's account, low and medium changes use SuperBiz's approval instead (the same cross-check as cross-gating). High changes need approval from everyone who is not the PR author.
- A PR with no change folder follows the medium rules.
- Release-ready requires no `event=revert` record.

## The 9 auto-merge conditions (`scripts/auto-merge-check.sh <change-dir> [--base main] [--record]`)

Prints `ALLOW` when every condition passes. Otherwise prints `DENY` with one reason per line.

1. `pod.yml` sets `auto_merge: low`.
2. The Risk in intent.md is `low`, and the gate 1 approval is not stale (the Risk was not lowered after approval).
3. No file in `git diff --name-only <base>...HEAD` matches `docs/risk-paths`.
4. Gates 1 to 3 are complete and not stale.
5. `review.md` has `blockers: 0`, `second_opinion: agree`, and a `reviewed_head` that matches HEAD.
   (Commits after reviewed_head that only touch files in this change's folder, such as review.md, do not count as code changes.)
6. `test_cmd` in pod.yml and `scripts/test-strength.sh` pass. If pod.yml sets `strength: off`, the result is always DENY,
   because an automated merge requires a test-strength result (see `docs/test-strength.md`).
7. No lines are deleted in `tests_dir` (default `tests/`). Tests may only be added.
8. Lines changed outside `docs/` and `tests_dir` total no more than `auto_merge_max_lines`.
9. At least `auto_merge_min_track` changes have passed gate 4, and none of the most recent `auto_merge_min_track` was reverted.

With `--record`, an ALLOW result appends this line to gates.log:

```
gate=4 role=auto by=auto-merge at=<ISO> blob=<hash of acceptance.md or -> head=<sha>
```

An agent may run `auto-merge-check.sh --record` followed by `gh pr merge --auto --squash` only when it prints ALLOW.
Agents never run `scripts/gate.sh` or `scripts/mark-revert.sh`.

## Acceptance after merge

- After an auto record, SuperBiz may sign gate 4 (cross) before SuperDev. SuperDev then signs as owner against the same acceptance.md.
- If `acceptance_hours` passes and SuperBiz has not signed, release-check reports that the change must not be released to production until SuperBiz accepts it.
- The post-merge acceptance (acceptance.md and the gate 4 signatures) goes to `main` in its own pull request. That pull request changes only `docs/`, so the auto record does not apply to it: it needs an approval from a pod member who did not open it.

## Revert

1. Revert the code: `git revert <commit>`, then open a PR as usual.
2. A person on the team (SuperBiz, SuperDev or escalation) records it:
   `scripts/mark-revert.sh docs/changes/NNN-slug "<reason>"`
   which appends the line `event=revert by=<email> at=<ISO> reason="..."`.
3. Result: release-check fails for that change, and auto-merge is disabled until `auto_merge_min_track` later changes have passed without a revert.

## GitHub setup

1. Add the GitHub logins to `pod.yml` (`superbiz_github`, `superdev_github`, `escalation_github`).
2. Run `scripts/sync-codeowners.sh` to generate `.github/CODEOWNERS` from `docs/risk-paths`, then commit it (`make check` verifies that they match).
3. Run `scripts/setup-github.sh <owner/repo>` to see what will be configured, then run it again with `--yes`.
   Branch protection needs a public repository or a paid GitHub plan for private ones; on a free plan the
   script stops with that message and `main` stays unprotected.
   - Enables auto-merge for the repository.
   - Protects main: the `pod-gates` check must pass, code owner review is required, stale reviews are dismissed on new commits, and force pushes are blocked.
4. CI (`.github/workflows/pod-gates.yml`) runs `make -f pod.mk pod-check` and `scripts/pr-check.sh`, which reads the PR author and approvers with `gh api`.
   GitHub approvals are tied to the signed-in account, so they are harder to fake than an email in git config.
