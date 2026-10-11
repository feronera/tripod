# Plan: Item count per order for support

References: intent.md (gate 1 passed, Risk: low), spec.md and ux-brief.md (gate 2 passed). ux-brief has no screen.

## Data shape
No new data. The function reads the existing record `_ORDERS[order_id]["items"]`, a `list[str]` (`app/orders.py:18-23`).
The count is `len()` of that list: each list entry counts once (E5), and status does not matter (E4).

`item_count(order_id) -> int` in `app/orders.py`, placed after `get_order`. It does three things in order, with no other branches:
1. `if not isinstance(order_id, str): raise OrderNotFound("Order not found")`. This comes first so `None`, numbers and unhashable ids such as lists never reach the dict lookup (E3). The same check is in `status_history` (`:118-119`).
2. `order = _ORDERS.get(order_id)`. If it is `None`, raise the same `OrderNotFound` (R2, E1). `""` ends here too.
3. `return len(order["items"])`. This is a new `int`, so changing it cannot change stored data (R4). Nothing is written (R3).

It reads `_ORDERS` directly rather than `get_order`, so it does not copy the list just to count it. The function has no `customer_id` parameter, on purpose (spec concern 8).

## Throughput checkpoint
- Blocking first steps: write failing tests in `tests/test_item_count.py`, check them with `make strength`, commit, then lock the tests.
- Independent workstreams: n/a: one function of about 6 lines in one file.
- Shared mutable state: `_ORDERS` and `_HISTORY` are module globals. The E2 test adds a temporary empty order, so `setUp` deep-copies both and `addCleanup` restores them, as `tests/test_status_report.py:33-37` does.
- Smallest safe decomposition: one unit (the function) that ends with `make test`, then `make check`.

## Parallel parts
none: one function in one file plus one test file. Splitting would cost more than it saves.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| tests/test_item_count.py (new) | Failing tests for R1-R4 and E1-E5, with save and restore of `_ORDERS`/`_HISTORY` | R1-R4 |
| app/orders.py | Add `item_count(order_id)` after `get_order`. No existing function changes. | R1-R4, R6 |

Risk-paths check (spec concern 1): neither path matches `docs/risk-paths`, so `Risk: low` still holds. No route, page or JSON field is touched (R5).

## Order of work
1. `/superdev:test-first`: write the tests in `tests/test_item_count.py`:
   - `A1001` gives 2, `A1002` gives 1, `A1003` gives 1, `A1004` gives 1, and each result is an `int` (R1, R4, E4).
   - `"A9999"` raises `OrderNotFound` with the message "Order not found" (R2, E1).
   - `None`, `3`, `""` and `["A1001"]` each raise `OrderNotFound`, not `TypeError` (E3).
   - A temporary order with `items: []` gives 0, and the order is gone after the test (E2).
   - A temporary order with `["T-shirt", "T-shirt"]` gives 2 (E5).
   - Deep copies of `_ORDERS` and `_HISTORY` are equal before and after a found call and a not-found call. The found call's result is asserted to be 2 in the same test, so a stub that returns None fails it (R3).
   - `get_order("A1001")` is unchanged after the call (R4).

   Run `make strength`, then commit.
2. Lock the tests: `touch .pod/lock-tests`.
3. Unit 1: add `item_count` as described in Data shape. Run `make test` until everything passes, including the existing suites (R5). Commit `feat(004)`.
4. Run `make check`.

## Risks
- A test leaves its temporary order in `_ORDERS` and later tests fail. To reduce: restore in `addCleanup` and run the whole suite, not one file.
- Someone later connects `item_count` to a customer route. That would show counts for other customers' orders (spec concern 8). To reduce: the docstring says "internal use, no ownership check". R5 forbids such a route in this change.
- A stored order without an `items` key would raise `KeyError`. No such order exists, and `set_status` keeps `items`. Accepted: guarding against bad stored data would need validation where data is written, which is out of scope.

## Proof
- `make test`, `make strength` and `make check` pass.
- R1, E4: the exact counts for `A1001` to `A1004`.
- R2, E1, E3: tests that the unknown id and the malformed ids raise `OrderNotFound` with the same message.
- R3: the before-and-after snapshot test, for both found and not-found calls.
- R4: the `int` type check, and `get_order` output is unchanged.
- E2, E5: the tests with temporary orders.
- R5: the existing tests in `tests/` pass with no edits, and the diff touches no route or page file.
- R6: the diff adds no import outside the standard library (it adds no import at all).

## Rollback
- Run `git revert <merge commit of 004>`. Nothing calls `item_count` and nothing is stored, so there is no data to restore.
- Afterwards, check that `make check` passes.

## Summary for SuperBiz
1. We will add one step that support can use to get the number of items in any order, so nobody has to count the list by hand.
2. Customers see nothing new. A wrong or missing order number gives the same "Order not found" message as other lookups do.
3. Low risk: it only reads data and can be removed in minutes. If an order lists the same item twice, it counts as 2, because the system does not store quantities.
