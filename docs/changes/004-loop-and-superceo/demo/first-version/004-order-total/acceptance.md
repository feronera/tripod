# Acceptance: Item count per order for support

References: intent.md (Success measure), PR: branch `change/004-order-total` (already auto-merged: `role=auto` line in gates.log, so this is acceptance after merge)

What changed, in plain words: support can now ask the system "how many items are in order X?" and get one number. Nothing changes for customers, and no order is touched.

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| 1. `item_count(order_id)` returns the number of items in an existing order | Tests `test_r1_e4_*` (A1001 gives 2; A1002, A1003, A1004 give 1; result is an `int`), as recorded in review.md | Review.md: all pass, `make test` 116 tests pass | Yes |
| 2. Raises OrderNotFound for an order that does not exist | Tests `test_r2_e1_*` and `test_e3_*` (unknown id, None, number, empty text, list) | Same "Order not found" error as the other lookups; no TypeError | Yes |
| 3. Never changes any order | Tests `test_r3_*` and `test_r4_*` (before/after snapshot of orders and history, for found and not-found calls) | Nothing changed | Yes |

## Demo steps
Plan.md gives no separate demo script, only a Proof list. The steps below are those Proof items. I could not run code in this session, so the actual results are taken from review.md (reviewed head `2a464a0`, `make check` pass), not from a run of my own.
1. Ask for the count of order A1001, then A1002, A1003 (pending) and A1004 (cancelled).
   - Expected result: 2, 1, 1, 1, whatever the status.
   - Actual result: covered by `test_r1_e4_*`, pass.
2. Ask for the count of an unknown order "A9999", and of a malformed id (none, 3, empty, a list).
   - Expected result: "Order not found" error each time, never 0.
   - Actual result: covered by `test_r2_e1_*` and `test_e3_*`, pass.
3. Ask for the count of an order with no items, and an order with the same item twice.
   - Expected result: 0, and 2.
   - Actual result: covered by `test_e2_*` and `test_e5_*`, pass.
4. Compare all orders and history before and after steps 1-2.
   - Expected result: identical.
   - Actual result: covered by `test_r3_*`, pass.

## Decision
Decision: accept

Reason: all three Success measures are met by passing tests, with no open blocker or major in review.md. The change is read-only, adds no route or page, and can be removed with `git revert`.

Accepted as risk (no one needs to check these again):
- The demo was not run by hand. Reason: the test suite already exercises every step, and I cannot run code in this session.
- Repeated items count once per list entry, because the data has no quantity field. It may differ from how support counted by hand; no Success measure depends on it (spec concern 5).
- The slug says "order-total" but the change is an item count (spec concern 4, already accepted at gate 2).
- Support has no web screen for this; it is a function only. A web entry would be a new intent.
- No measurable business result yet (fewer than 3 of 40 tickets needing a hand count). It can only be measured after support starts using it; I set no date, because none was given in the intent. A date needs a SuperBiz decision.
