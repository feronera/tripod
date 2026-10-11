# Plan: Count the notes on an order for support

References: intent.md, spec.md, ux-brief.md

## Data shape
- `Note(NamedTuple)`: `order_id: str`, `text: str`. It cannot be changed once stored, like `StatusUpdate` (`app/orders.py:26`).
- `_NOTES = {}`: maps order id to a list of `Note`, append-only, kept next to `_HISTORY` in `app/orders.py`.
  Notes are stored per order, so one order's notes cannot count toward another (E5).
- `add_note(order_id, text)` is the only writer. It checks everything first (unknown order → `OrderNotFound`,
  blank text → `ValueError`) and only then appends, so a rejected call stores nothing (E4).
- `note_count(order_id)` returns `len(_NOTES.get(order_id, ()))` after checking that `order_id` is a `str` and is in `_ORDERS`.
  It returns an `int` and never writes (R1, R2). A missing key gives 0 (E1). It never returns note text.

## Throughput checkpoint
- Blocking first steps: failing tests in `tests/test_order_notes.py`, then lock the tests.
- Independent workstreams: n/a: one file with about 20 lines of code.
- Shared mutable state: `app/orders.py` module state (`_ORDERS`, `_NOTES`). Tests patch both with `mock.patch.dict`, as `tests/test_order_server.py:71` does.
- Smallest safe decomposition: (1) `Note` + `_NOTES` + `add_note`, (2) `note_count`. Each unit ends with `make test` passing.

## Parallel parts
none: the change is small and all of it is in one file (`app/orders.py`). Splitting it would make two parts edit the same file.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| app/orders.py | Add `Note`, `_NOTES`, `add_note`, `note_count` | R1, R2, R3, R5 |
| tests/test_order_notes.py | New: tests for E1–E5, the read-only check, and a check that no route exposes the count | R1–R4 |
| app/server.py | No change. A test confirms that `ROUTES` and the page never show the count or note text | R4 |

## Order of work
1. Write failing tests for E1–E5, R2 (count is stable, and stored data is unchanged after a deepcopy compare) and R4 (every `ROUTES` path response has no count and no note text), then commit.
2. Lock the tests (`touch .pod/lock-tests`).
3. Add `Note`, `_NOTES` and `add_note` with checks before the write. `make test` passes for the E4 tests.
4. Add `note_count` with the `str` check, the order check and `len`. `make test` and `make strength` pass.

## Risks
- Real notes may live outside this repo (spec flagged concern). Accepted: the stand-in is two functions and one dict, cheap to replace. Reason: nothing in the repo points to another store.
- Tests could leak notes into each other through module state. Reduced by patching `_NOTES` and `_ORDERS` in every test.
- The strength check fails if a test only asserts "no error". Reduced by asserting exact counts (0, 1, 3) and exact stored lists.
- Any code in the process can call `note_count`, because no support sign-in exists. Accepted per the spec: there is no route, so no new access path.

## Proof
- `make test` and `make strength` pass.
- R1/E1/E5: counts are 0, 1 and 3 on separate orders. R2: the count is the same after repeated calls, and `_NOTES`/`_ORDERS` are equal to a deepcopy taken before.
- R3/E2/E3: unknown id, `None`, `1` and `""` raise `OrderNotFound("Order not found")`, never `TypeError`.
- E4: blank text raises `ValueError` and an unknown order raises `OrderNotFound`. Both leave `_NOTES` unchanged.
- R4: the route test, plus a demo of `/orders/A1001` showing no notes. R5: review of the imports in the diff.

## Rollback
- `git revert <feat(007) commits>`. Nothing else calls the new functions and no data is persisted, so the revert is safe. Afterwards run `make check`.

## Summary for SuperBiz
1. Support gets a quick way to find out how many notes an order has, without counting by hand.
2. Customers see nothing different. Only internal tools can ask for the count.
3. This uses a simple stand-in place for notes. If the real notes are kept somewhere else, a follow-up change will be needed, and it may carry higher risk.
