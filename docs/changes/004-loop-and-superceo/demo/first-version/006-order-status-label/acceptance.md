# Acceptance: Status label lookup for support

References: intent.md (Success measure), PR: branch `change/006-order-status-label` (auto-merge recorded in gates.log, `role=auto`; this is acceptance after merge)

What changed, in plain words: support scripts get one new lookup, `support_status_label(code)`. It turns an order status code such as "packing" into the customer wording ("Preparing order"), and shows "Unknown status" for anything else. Customers see nothing different, and no order is changed.

## Success measure check
Results come from the demo steps in plan.md (Proof) and the results recorded in review.md. I could not run commands in this session, so I did not re-run them. Gate 3 and the review checks were already verified by scripts, so I did not repeat them.

| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| 1. Known code returns its label from STATUS_LABELS | Test loops over every key of STATUS_LABELS (plan Proof, R1) | review.md: `make check` pass, 118 tests OK | Yes |
| 2. Any other value returns "Unknown status", no error | Tests for "", None, 0, [], {}, "Packing", " packing ", "Shipped" (R2) | Same run: pass | Yes |
| 3. Never changes any order | Before/after comparison of orders, history and STATUS_LABELS (R3) | Same run: pass. The function has no write path | Yes |

## Demo steps
1. Run `make test` and `make strength`.
   - Expected result: all tests pass and no weak tests are found.
   - Actual result: per review.md, 118 tests OK and no weak tests.
2. Call `support_status_label("packing")`.
   - Expected result: the customer wording, "Preparing order" (plan.md summary).
   - Actual result: covered by the R1 test over all known codes (pass). Not run by hand.
3. Call `support_status_label` with "Shipped", None and [].
   - Expected result: "Unknown status" each time, no error.
   - Actual result: covered by the R2 tests (pass). Not run by hand.
4. Check that the customer page and `status_label("x")` still return the raw code.
   - Expected result: unchanged (R4).
   - Actual result: existing tests in `tests/test_orders.py` and `tests/test_status_report.py` pass.

## Decision
Decision: accept (proposed for SuperBiz to confirm)

Reason: all three Success measure items pass, with 0 blockers and 0 majors in review.md and `make check` green. The change is read-only and low risk, and it can be reverted with `git revert`.

Decided here: the name `support_status_label` satisfies the intent wording `status_label(code)`. The intent says "within this change", and `status_label` is already used by the customer page and returns the raw code for unknown values (R4). Reusing that name would change what customers see.

Accepted risks:
- Two similar function names may confuse readers. Both docstrings name the other.
- The `isinstance(code, str)` guard would miss a non-str key added to STATUS_LABELS later. Today every key is a str.
- The branch diff adds `docs/superceo/2026-10-11.md`, which is not in plan.md. It is docs only and has no effect on behavior.
- The 4 of 40 tickets figure (the problem in intent.md) can only be checked after support scripts start calling the function. No caller exists yet. Measure it in the first weekly ticket review after a script adopts it. I did not invent a date. Until then, this is an open follow-up.
