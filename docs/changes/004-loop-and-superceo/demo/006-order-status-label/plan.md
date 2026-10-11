# Plan: Status label lookup for support

References: intent.md, spec.md, ux-brief.md

## Data shape
The existing table `STATUS_LABELS` (`app/orders.py:9`, code -> label) is the only data, read and never written.
One constant is added next to it: `UNKNOWN_STATUS_LABEL = "Unknown status"`.
The new function `support_status_label(code)` is one guarded lookup: `STATUS_LABELS[code]` only when `code` is a
`str` key of the table, otherwise `UNKNOWN_STATUS_LABEL`. The `isinstance(code, str)` guard makes unhashable inputs
(list, dict, E1) impossible to reach the dict, so no `try/except` is needed. Exact match only (E2, E3).
Name decision: `support_status_label`, because `status_label` already exists with different behavior for unknown
codes and is used by the customer page and `status_counts` (R4). The name says who it is for.

## Throughput checkpoint
- Blocking first steps: failing tests for R1-R3 and E1-E3 in a new test file, then `.pod/lock-tests`.
- Independent workstreams: n/a: one function and one constant in one file.
- Shared mutable state: n/a: read-only lookup; `_ORDERS`, `_HISTORY` and `STATUS_LABELS` are not written.
- Smallest safe decomposition: (1) tests committed and locked, (2) constant + function, ending with `make check`.

## Parallel parts
none: the whole change is about 5 lines in one file; splitting adds coordination with no gain.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| tests/test_status_label_support.py | New tests: every `STATUS_LABELS` key, unknown/malformed inputs, no mutation | R1, R2, R3 |
| app/orders.py | Add `UNKNOWN_STATUS_LABEL` and `support_status_label`; `status_label` untouched | R1, R2, R3, R4 |

## Order of work
1. Write failing tests from R1-R3 and E1-E3 in `tests/test_status_label_support.py`, then commit.
2. Lock the tests (`touch .pod/lock-tests`).
3. Add the constant and `support_status_label` with a docstring saying it is for support scripts and how it differs
   from `status_label`; `make check` passes.

## Risks
- Two similar functions confuse readers (accepted in spec): reduced by docstrings on both naming the other.
- Someone "fixes" `status_label` instead: R4 is guarded by the existing tests in `tests/test_orders.py` and the order page tests.
- Mutation test (R3) passes trivially: the test snapshots deep copies of `_ORDERS`, `_HISTORY` and `STATUS_LABELS`
  and compares after calling with known, unknown and malformed codes; `make strength` confirms the tests fail when the function returns None.
- No sensitive path in `docs/risk-paths` is touched, so Risk: low holds.

## Proof
- `make test` and `make strength` pass (`make check` in CI).
- R1: test loops over every key of `STATUS_LABELS` and asserts the matching label.
- R2: tests for "", None, 0, [], {}, "Packing", " packing ", "Shipped" each return "Unknown status" without raising.
- R3: before/after equality of orders, history and `STATUS_LABELS`.
- R4: existing tests unchanged and passing; `status_label("x")` still returns "x".

## Rollback
- `git revert <merge commit>`; then `make test` passes. Nothing else calls the new function yet, so no caller breaks.

## Summary for SuperBiz
1. Support gets one new lookup that turns an order status code into the wording customers already know.
2. Customers see no change; support scripts can show "Preparing order" instead of "packing", or "Unknown status" for anything unexpected.
3. Low risk: nothing is changed or stored. The lookup is named `support_status_label`, not `status_label`, because that name is already used by the customer page.
