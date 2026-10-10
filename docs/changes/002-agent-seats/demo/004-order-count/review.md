blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: a48f38ecf4dbc271d82d1bca53162726b484a9b5

# Review: Order count per customer for support

## Blocker
- none

## Major
- none

## Minor
- tests/test_order_count.py (R6): the check is a text match on app/server.py and app/order_page.py; an import through a third module would not be caught. Matches the spec wording.
- tests/test_order_count.py (R4): the test name could say int.
- E3 is covered indirectly (C001 -> 2 of 4 orders, C002 -> 1), not by a dedicated test.

## Second opinion (reviewer-second)
- claude-sonnet-5-5, read-only, session 6d11a474-342d-40f3-940a-de9370b84b0d: blockers_found 0, no_blocker_verdict agree.

## After the lock (disclosed)
- tests/test_order_count.py was edited after `.pod/lock-tests`: test-strength flagged test_reads_only and test_not_reachable_from_customer_pages as weak (they passed with order_count returning None). Each now also asserts a count. No assertion was removed. The test-first step should have run test-strength before locking; in this demo it did not.

## Pre-existing failure, not from this change
- `make check` fails in `gate-check --all` on change 003's plan.md (its parallel parts have no `tests:` lines, a rule added in kit 0.5.6 after change 003 was signed). Change 004 does not touch change 003. `make test` and `make strength` pass.

## Checks
- make test: pass (115 tests)
- scripts/test-strength.sh: pass (after strengthening two tests it flagged)
