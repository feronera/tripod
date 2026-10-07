# AGENTS.md

Rules for every agent in this repository (Claude Code reads them through CLAUDE.md).

## Pod
- The pod has two humans: **SuperBiz** (PO, PM, BA, Designer: what and why) and **SuperDev** (SA, Dev, QA, Deploy, MA: how, and whether it is safe).
- Agents draft the work of every role. Humans make the decisions at the gates.
- Member names and emails are in `pod.yml`.

## Gates
| Gate | Artifact | Owner | Cross |
|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev |
| 3 | plan.md | SuperDev | SuperBiz |
| 4 | acceptance.md + PR | SuperDev | SuperBiz |

- `Risk: high` in intent.md requires an additional escalation signature at gates 2 and 4.
- Gate 3: plan.md must contain `## Data shape`, `## Throughput checkpoint` and `## Parallel parts` (checked by script).
- Gate 4 is split into merge-ready (`scripts/gate-check.sh <dir> 4`) and release-ready (`scripts/release-check.sh <dir>`).
  Merge rights by risk are in `docs/merge-by-risk.md`.
- Details are in `docs/gates.md` and `docs/risk-tiers.md`.

## Rules that must never be broken
1. Agents must not run `scripts/gate.sh` or `scripts/mark-revert.sh`, and must not edit `gates.log` by hand.
   Approvals and revert records belong to humans only.
2. When `.pod/lock-tests` exists, do not edit files in `tests/`. If a test looks wrong, stop and tell the human.
3. When `.pod/kill-switch` exists, stop work immediately. Never delete this file.
4. Do not merge or push to main until `scripts/gate-check.sh --all` passes and the latest change is merge-ready at gate 4.
   The only exception for agents: run `scripts/auto-merge-check.sh <dir> --record`, then `gh pr merge --auto --squash`,
   and only when the command prints `ALLOW` (for medium risk, SuperDev signs gate 4 first; for high risk, a human merges).
5. Never invent numbers. If you do not know, put it under Open questions.
6. Never copy personal data from logs into documents or code.
7. Never edit an artifact that has passed a gate without saying so, because the approval becomes stale.
8. Tests must check real behavior. `scripts/test-strength.sh` must pass (it is part of `make check`).
9. Fix bugs at the root cause: reproduce first, then write a failing test before the fix (`/superdev:bug-fix`).

## Where the work lives
- Each change's artifacts are in `docs/changes/NNN-slug/`
  (intent.md, ux-brief.md, spec.md, plan.md, review.md, acceptance.md, runbook.md, gates.log).
- Start a new change only with `scripts/new-change.sh <slug>`.
- Templates are in `docs/templates/`.
- Sensitive paths are listed in `docs/risk-paths`. A change that touches these paths is high risk.

## Stack
- Python 3 standard library only. Do not add dependencies.
- Code is in `app/`, tests are in `tests/` (unittest), per `code_dirs` and `tests_dir` in `pod.yml`.

## Commands
- `make setup`: check tools and prepare the `.pod/` folder.
- `make test`: run `test_cmd` from `pod.yml` (all unit tests).
- `make strength`: `scripts/test-strength.sh` finds tests that still pass when every function in app/ returns None (see `docs/test-strength.md`).
- `make check`: tests, strength, the CODEOWNERS check and `scripts/gate-check.sh --all` (CI runs this).
- `scripts/auto-merge-check.sh <dir> [--base main] [--record]`: ALLOW or DENY for an automated merge.
- `scripts/release-check.sh <dir>`: whether the change is ready to release to production.
- `make metrics CHANGE=docs/changes/NNN-slug`: time from intent to each gate.
