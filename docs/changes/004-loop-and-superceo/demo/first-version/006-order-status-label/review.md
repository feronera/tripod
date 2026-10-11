blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: 22a3a51a6c2a5c85d384d8ff294bde07c61bf8dd

# Review: Status label lookup for support

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.

How the review ran: there was no subagent tool, so each lens ran through headless `claude -p` with the
`reviewer` / `reviewer-second` prompts and the diff, spec.md, plan.md and the checklist.
Security, correctness and tests ran on claude-opus-5-5; the second opinion ran on claude-sonnet-5-5.

## Blocker
- none

## Major
- none. R1–R4 and E1–E4 each have a test (`tests/test_status_label_support.py`). The scope matches the plan's "Files to change". Rollback is `git revert`, and nothing calls the new function yet.

## Minor
- `app/orders.py:88` The `isinstance(code, str)` guard would miss a non-str key added to `STATUS_LABELS` in the future. Accepted: today every key is a str, and the plan chose this guard (Data shape).
- `app/orders.py:88` A `str` subclass (e.g. a `StrEnum`) equal to a key matches. That fits E2's exact-value match. No test covers it, and none is needed.
- `tests/test_status_label_support.py:33` R3 snapshots `_HISTORY`, which may be empty when the file runs alone, so changes to existing history lists aren't exercised. Accepted: the function has no write path. Tests are locked, so I made no change.
- `spec.md` Flagged concerns cites `app/orders.py:72` for `status_label`, which is now line 74. This is a stale doc reference only. I left it unedited so the gate 2 approval doesn't go stale.
- The branch diff also adds `docs/superceo/2026-10-11.md`, which plan.md doesn't list. It is docs only, not code, and has no effect on behavior.
- Open from spec: SuperBiz confirms at acceptance that `support_status_label` satisfies the intent wording `status_label(code)`.

## Reviewer questions answered
- Lock: `tests/` has one commit on this branch (a816f50, before the implementation in 103f404). It has not been edited since, and `.pod/lock-tests` exists.
- R4: the existing raw-code behavior is still covered by `tests/test_status_report.py:99,107,123` (status_counts) and the order tests. All pass.

## Second opinion (reviewer-second)
- claude-sonnet-5-5: blockers_found 0, no_blocker_verdict agree. It raised only Minors, which overlap with the ones above. It did not see the first reviewers' results.

## Checks
- `make check`: pass (118 tests OK, CODEOWNERS OK, gate-check --all OK)
- `scripts/test-strength.sh`: pass (118 tests, no weak tests)
