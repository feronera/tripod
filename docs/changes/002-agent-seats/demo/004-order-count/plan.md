# Plan: Order count per customer for support

References: intent.md, spec.md

## Data shape
No new data. `_ORDERS` (dict order_id -> {customer_id, status, items}) already holds every order; the count is the number of entries whose `customer_id` equals the argument. Nothing is stored, so R3 (no change to orders or history) holds by construction.

## Throughput checkpoint
- Blocking first steps: failing tests for R1-R6 and E1-E4
- Independent workstreams: n/a: one function and its tests
- Shared mutable state: app/orders.py (read-only use of `_ORDERS`)
- Smallest safe decomposition: tests, then the function; each ends with `make test` passing

## Parallel parts
none: one small function in one file

## Files to change
| File | What changes | Requirement |
|---|---|---|
| app/orders.py | add `order_count(customer_id)`: `TypeError` for a non-string id, else `sum(1 for o in _ORDERS.values() if o["customer_id"] == customer_id)` | R1, R2, R3, R4, R5 |
| tests/test_order_count.py (new) | tests for R1-R6 and E1-E4 | all |

## Order of work
1. Write failing tests in tests/test_order_count.py from the requirements and edge cases, then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. Add `order_count` to app/orders.py; `make test` passes

## Risks
- None beyond the accepted C1 and C2 in spec.md. The function reads `_ORDERS` only and is not imported by app/server.py or app/order_page.py (R6, checked by a test).

## Proof
- `make test` and `make strength` pass
- R1: C001 -> 2; R2: "C999" and "" -> 0; R3: `_ORDERS` and `_HISTORY` equal before and after; R4: result is an `int`; R5: None and 42 raise TypeError; R6: neither app/server.py nor app/order_page.py mentions `order_count`; E4: a cancelled order (C003) counts 1

## Rollback
- `git revert <merge commit>`; nothing else uses the function, so nothing else changes.

## Summary for SuperBiz
1. Support gets one call that says how many orders a customer has.
2. Customers see no change; it is not reachable from the customer pages.
3. Risk: an unknown customer id also shows 0 (accepted in spec C1), and cancelled orders are counted (spec C2).
