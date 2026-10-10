# Plan: Order counts by status for support

References: intent.md, spec.md

## Data shape
No new data. Count `_ORDERS` entries whose customer_id matches, grouped by status, with collections.Counter.

## Throughput checkpoint
- Blocking first steps: failing tests for the requirements
- Independent workstreams: n/a: one function
- Shared mutable state: app/orders.py (read-only)
- Smallest safe decomposition: tests, then the function

## Parallel parts
none: one small function

## Files to change
| File | What changes | Requirement |
|---|---|---|
| app/orders.py | add `status_counts(customer_id)`: TypeError for a non-string id, else `dict(Counter(o["status"] for o in _ORDERS.values() if o["customer_id"] == customer_id))` | R1, R2, R3 |
| tests/test_status_counts.py | tests for R1, R2, R3 and E1-E3 | all |

## Order of work
1. Failing tests, then lock them
2. Add the function; make test passes

## Risks
- None.

## Proof
- R1: C001 -> shipped 1, delivered 1; R2: data unchanged; R3: None raises TypeError

## Rollback
- git revert the merge commit.

## Summary for SuperBiz
1. Support gets the order counts per status for a customer in one call.
2. Customers see no change.
3. No risks beyond a read-only function.
