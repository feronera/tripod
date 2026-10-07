---
name: merge
description: Merge a reviewed change by its risk tier. Low risk may auto-merge only when scripts/auto-merge-check.sh prints ALLOW; medium needs SuperDev to sign gate 4 first; high stops and hands over to humans. Use when the user says "merge", "merge ตาม risk", "รวมเข้า main", "ปิด PR", "auto-merge".
---

# Merge by risk (SuperDev: Deploy)

Goal: merge into main according to the rights for each risk tier in `docs/merge-by-risk.md`.

## Before you start
1. The change's `review.md` exists and shows `blockers: 0`.
2. The PR is open and the CI job `pod-gates` passes.
3. Read the Risk from intent.md, and check whether the diff touches any path in `docs/risk-paths`
   (`git diff --name-only main...HEAD`). If it does, treat the change as high.

## Risk: low
1. Run `scripts/auto-merge-check.sh docs/changes/NNN-slug`.
2. If it prints `DENY`, give the human every reason line, then follow the medium flow (or fix the reasons).
3. If it prints `ALLOW`, run `scripts/auto-merge-check.sh docs/changes/NNN-slug --record`,
   then commit and push gates.log: `git commit -m "chore(NNN): auto-merge record" -- docs/changes/NNN-slug/gates.log`.
4. Run `gh pr merge --auto --squash` (the gate-guard hook checks again first).
5. Tell SuperBiz to accept the change with `/superbiz:acceptance` and sign gate 4 within
   `acceptance_hours` in pod.yml, before release to production.

## Risk: medium
1. acceptance.md must already exist (SuperBiz drafts it with `/superbiz:acceptance`).
   Ask SuperDev to review review.md and acceptance.md, then sign gate 4 themselves
   (`scripts/gate.sh docs/changes/NNN-slug 4`).
2. Only after `scripts/gate-check.sh docs/changes/NNN-slug 4` passes, run `gh pr merge --auto --squash`.
3. SuperBiz signs gate 4 (cross) before release. If SuperBiz edits acceptance.md, SuperDev's signature becomes stale and must be signed again.

## Risk: high
- Stop. Never merge yourself. Tell SuperDev, SuperBiz and the escalation person that all three must sign gate 4
  and all three must approve the PR on GitHub. Then a human merges.

## Do not
- Run `scripts/gate.sh` or `scripts/mark-revert.sh`, or edit `gates.log` by hand
  (the `role=auto` line must come from `--record` only).
- Run `--record` or `gh pr merge` when the result is not `ALLOW`.
- Lower the Risk in intent.md to make auto-merge possible.

## When done
Tell the human the next step is `/superdev:release`, which uses `scripts/release-check.sh`.
