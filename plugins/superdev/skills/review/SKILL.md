---
name: review
description: Review the branch diff with three reviewer lenses in parallel (security, correctness, tests and edge cases) plus an independent second opinion from reviewer-second on another model, fix Blockers, and write docs/changes/NNN-slug/review.md with the machine-readable header that auto-merge-check reads. Use when the user says "รีวิวโค้ด", "ตรวจ PR", "review", "code review", "ready for gate 4".
---

# Review (SuperDev: QA)

Goal: no Blockers left, a second opinion that agrees, and a `review.md` for gate 4 and merge.

## Steps
1. Check that the working tree is clean (`git status`), then run `git diff main...HEAD`, `git log main..HEAD --oneline`
   and `make check` (including `scripts/test-strength.sh`).
2. Send three `reviewer` agents in parallel in a single message. Each gets the diff, spec.md, plan.md
   and the REVIEW checklist below, and each focuses on a different lens:
   - security: access control, personal data, secrets, input handling
   - correctness: are the requirements in spec.md implemented completely and correctly?
   - tests and edge cases: does every edge case in spec.md have a test, and do the tests check real behavior?
3. Merge the results into one list and remove duplicates.
4. Fix every Blocker, then run `make check` again.
   - If a Blocker is in a locked test, do not edit the test. Tell the human.
5. Major: fix it, or write the reason for not fixing it and let the human decide. Unfixed Majors count toward `majors_open`.
6. Minor: record it. No need to fix it in this change.
7. Send the reviewers again until there are no Blockers, and commit all fixes.
8. Second opinion: send the `reviewer-second` agent to review the latest diff with the same checklist.
   - Send only the diff, spec.md, plan.md and the checklist. Never send the first reviewers' results.
   - `agree`: reviewer-second finds no Blocker the first reviewers missed, and does not dispute the "no Blocker" result.
   - `disagree`: it finds a new Blocker or disputes the result. Fix it, then go back to step 2.
9. Write `docs/changes/NNN-slug/review.md` from `docs/templates/review.md`.
   The first 4 lines must be this header (key names must match exactly, because `scripts/auto-merge-check.sh` reads them):
   ```
   blockers: <int>
   majors_open: <int>
   second_opinion: agree | disagree
   reviewed_head: <git sha of the reviewed HEAD>
   ```
   Get `reviewed_head` from `git rev-parse HEAD` at review time. Follow the header with the findings.
10. Commit review.md: `git commit -m "docs(NNN): review"`.
    Commits after reviewed_head that only touch files in `docs/changes/NNN-slug/` do not make the review stale,
    but any later change to code or tests needs a new review.

## REVIEW checklist
Blocker
- A requirement in spec.md has no code or test behind it.
- A user can see other users' data, or an error reveals that other users' data exists.
- Personal data, secrets or tokens in code, tests or logs.
- Tests edited or deleted after locking, or `make check` fails.
- `scripts/test-strength.sh` fails (a test still passes when every function in app/ returns None).
- A dependency outside the Python standard library.

Major
- An edge case in spec.md has no test.
- Code goes beyond the scope of plan.md or touches Out of scope.
- No rollback method as stated in plan.md.

Minor
- Unclear names, duplicated code, UI copy that does not match ux-brief.md.

## When done
Write a gate 4 summary in the PR description:
1. What changed, citing R1, R2, ...
2. The `make check` result
3. Remaining Majors and Minors, with reasons
4. Demo steps for SuperBiz to use in `/superbiz:acceptance`
Tell the human the next step is `/superdev:merge`, which merges according to the change's Risk.
