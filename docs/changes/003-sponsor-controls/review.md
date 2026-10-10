blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: acc39f7dc8f919c79d5988be07e68f3d287ede93

# Review: Sponsor controls (budget, ceiling, automatic stops, daily digest)

Three reviewer lenses on Opus 5.5 (security and bypass, correctness, tests and edge cases), then an independent second opinion on Sonnet 5.5 that did not see the first results.

## Blocker (fixed)
- **B1 (security): `TRIPOD_NOW` set to a future time turned off every time-based stop, and nothing recorded it.** Fix: `TRIPOD_NOW` can only move the clock back, and later events stay in every window, so it can only make limits stricter. Tests: ClockTests.

## Major (all fixed)
- The ledger read only the working tree, so a revert on main did not pause other branches. It now also reads each change's logs on the base branch (BaseBranchTests).
- Forged resume or signature lines reset the refusal counter. They now count only from the sponsor or a member (IdentityTests).
- `usd=nan`, a negative amount or `inf` turned budgets off, and a bad time dropped a cost. Such amounts now count as unknown, and an undated record still counts toward its change (AmountTests).
- `docs/model-prices` could be edited to make agent work look free. It is now a governance file (FileTests).
- `digest --write` followed symlinks. It now refuses them (FileTests).
- A rename hid the forbidden source path. `--no-renames` fixes it (FileTests).
- A change's own auto record counted against `agent_merges_per_day` when CI re-checked it, and records were counted instead of changes (MergesPerDayTests).
- The digest's "stops in force" used a different formula than agent-sign and missed refusals outside the window. Both now use the same functions (DigestStopTests).
- The hook read every log on every tool call: about 880 ms at 40,000 lines. It now reads only the current change and the day's tail of each log: 34 ms (HookSpeedPathTests).
- Tests were missing for: the day-budget warning, "resume does not lift a budget or a revert" (R7), time-zone offsets (E6), the digest in Pod mode (E7), and the refusing side of E5. All are added.

## Minor
- Accepted, and documented in docs/autonomous.md under "Limits you accept":
  - parallel agent-sign starts can overshoot by one estimate per run;
  - unmerged branches do not see each other;
  - failed runs are not counted as refusals;
  - the budget warning also reaches people's sessions.
- The digest's per-change line uses one space where the ux-brief shows two.
- An identical line in both the base branch and the working tree is read once. Two identical records written in the same second would collapse into one, which errs toward fewer refusals.
- The demo found and fixed this before review: the digest listed the day budget but not per-change budgets under stops in force.

## Second opinion (reviewer-second)
- Sonnet 5.5, without the first results: blockers_found 0, no_blocker_verdict agree, Majors none.

## Checks
- `make check`: pass (317 tests, test-strength, CODEOWNERS, gate-check)
- `claude plugin validate --strict`: pass ×3
- Tests were locked at d61d382. Later test edits, all approved by the PO:
  - the --hours window;
  - pinned gate-1 times in SponsorRepo;
  - 0.9.0 version asserts;
  - the new file tests/test_sponsor_review.py.

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
