# Spec: Item count per order for support

References: intent.md, ux-brief.md

## Requirements
- R1: The system must provide `item_count(order_id)` in `app/orders.py` that returns the number of items in an existing order as an `int`. Example: `A1001` returns 2, `A1002` returns 1. (verified by: unit test against the sample orders in `_ORDERS`)
- R2: The system must raise `OrderNotFound` from `item_count` for an order id that does not exist, the same exception class the other lookups use. (verified by: unit test with an unknown id such as `"A9999"`)
- R3: The system must not change any order, status or history when `item_count` is called, including when it raises. (verified by: unit test that snapshots `_ORDERS` and `_HISTORY` before and after, for both found and not-found calls)
- R4: The system must return an `int` that is independent of stored data, so editing the result cannot change stored orders (a plain `len` of the items list satisfies this). (verified by: unit test that the result is an `int` and that `get_order` output is unchanged after the call)
- R5: The system must keep all existing behavior of `app/orders.py` and `app/order_page.py` unchanged: no customer page, route or JSON field is added or modified. (verified by: the existing test suite still passes in `make test`)
- R6: The system must use the Python 3 standard library only and add no dependency. (verified by: review of the diff and `make check`)

## Edge cases
- E1: Order id does not exist: raise `OrderNotFound("Order not found")`. Never return 0 for a missing order, so "empty order" and "no such order" cannot be confused.
- E2: Order exists with an empty items list: return 0. No such order exists in the sample data, so the test must build one in a way that does not leave data behind in `_ORDERS`.
- E3: Malformed order id (`None`, a number, an empty string, a list): raise `OrderNotFound`, not `TypeError`. `status_history` already does this for non-string ids (`app/orders.py:118-119`). An unhashable id such as a list would make `_ORDERS.get` raise `TypeError`, so the type check must come first.
- E4: Cancelled, pending or delivered orders (`A1004`, `A1003`, `A1002`): the count is the number of items on the order, regardless of status.
- E5: Repeated items in one order (for example two "T-shirt" entries): count each list entry. Quantity is not a field in the current data model.
- E6: Permissions: support staff look up any order, so the function has no `customer_id` parameter. It must not be exposed to customers (R5, Out of scope). Customer-facing functions keep their ownership check unchanged.
- E7: UX states from ux-brief.md: this change has no screen, so there are no empty, loading or error states. The only error is the `OrderNotFound` in E1 and E3.

## Flagged concerns
Every concern has one of two outcomes. **Answered** means this spec shows the evidence and nothing is left to decide. **Accepted as risk** means the spec states the position, the risk that remains and who confirms it. The named person confirms by signing gate 2 with the position unchanged, and an agent cannot sign for them. Any change to a position after signing makes the approval stale.

### Register (one line per concern)
| # | Concern | Outcome | Who confirms at gate 2 |
|---|---|---|---|
| 1 | Risk tier | Answered | none (SuperDev re-checks at gate 3) |
| 2 | Line references | Answered (re-checked against `app/orders.py` in this revision) | none |
| 3 | Support role in the code | Answered | none |
| 4 | Slug `004-order-total` vs item count | Accepted as risk | SuperBiz |
| 5 | "Number of items" means list entries | Accepted as risk | SuperBiz |
| 6 | Intent says "Open questions: None" | Accepted as risk | SuperBiz |
| 7 | Where the function lives, who can call it | Accepted as risk | SuperDev |
| 8 | No ownership check | Accepted as risk | SuperDev |
| 9 | Gate 1 check | Answered: gate 1 passed and was verified by `scripts/gate-check.sh`. It is not re-checked here. | none |
| 10 | Repeated-item counting in "3 of 40 tickets" | Accepted as risk (see below) | SuperBiz |

Items 4 to 8 and 10 are decided here with a reason. Signing gate 2 with this text unchanged is the confirmation, and it is the only step left.

### Answered
- **Risk tier.** `Risk: low` holds. Files touched: `app/orders.py`, a file under `tests/`, and `docs/changes/004-order-total/`. None matches a glob in `docs/risk-paths` (`app/auth*`, `app/payment*`, `**/migrations/**`, `.github/**`, `pod.yml`, `scripts/**`, `plugins/**/hooks/**`). The change is read-only, returns a count only, and has no customer view. If the plan adds a file that matches, the risk becomes high and this spec must be redone. SuperDev re-checks the file list at gate 3.
- **Line references.** Checked against `app/orders.py`: sample orders at `:18-23`, `get_order` ("internal use") at `:64-69`, `status_for_customer` at `:95`, `status_history` at `:111` with its non-string id check at `:118-119`.
- **Support role in the code.** A search of `app/` for "support" and "role" finds no support role or permission in `app/server.py` or `app/auth_demo.py`. The only hits are contact-support copy and the `role="status"` attribute in `app/order_page.py` and `app/static/order_page.js`. No existing access control applies, and none is added.

### Accepted as risk (confirmed by the named signer at gate 2)
- **Slug `004-order-total` does not match the intent (SuperBiz).**
  - Evidence: Problem, Success measure and the function name in `intent.md` all say item count. `_ORDERS` has no price (`app/orders.py:18-23`), so a money total could not be built.
  - Position: the change is the item count. The slug is a label only.
  - Risk accepted: a reader may expect a money total. Mitigation: Out of scope excludes totals, prices and tax by name. A rename is not done, because it would make the gate 1 signature stale.
- **"Number of items" means list entries (SuperBiz).**
  - Evidence: the data model has a list of item names and no quantity field (`app/orders.py:19-22`), so list entries are the only thing that can be counted.
  - Position: count each list entry (E5).
  - Risk accepted: support may count repeated items differently from the list. The intent says only "3 of 40 tickets last week" and does not say how repeated items were counted, and this agent does not know. No success measure depends on it, since measure 1 is "the number of items in an existing order". If quantities are added later, that is a new change.
- **`intent.md` says "Open questions: None" and "Status: draft" (SuperBiz).**
  - Position: `intent.md` stays unchanged, because editing it makes the signed gate 1 stale. This section is the record of the questions the spec raised.
  - Risk accepted: the intent and the spec differ on open questions. None of them changes a success measure: measures 1 to 3 map to R1, R2 (with E1, E3) and R3.
- **Where the function lives and who can call it (SuperDev).**
  - Position: a plain internal function in `app/orders.py`, like `get_order`. No route, page or endpoint exposes it (R5, Out of scope). Support reaches it by calling the function.
  - Risk accepted: support has no web way in. Web access is a separate change with its own intent.
- **No ownership check, unlike the other lookups (SuperDev).**
  - Evidence: `status_for_customer` and `status_history` take a `customer_id` and hide other customers' orders (`app/orders.py:95-103`, `:111-120`). Support staff look up any order, so `item_count` takes only `order_id`. It shares the `OrderNotFound` class and message (R2).
  - Position: no `customer_id` parameter, deliberately.
  - Risk accepted: someone later wires `item_count` to a customer-facing route and exposes other customers' orders. R5 and Out of scope forbid that here, and the function returns a count only, with no personal data. Whoever adds such a route must add the ownership check.

## Open questions
None block this change. Decided with a default and a reason:
- **How repeated items were counted in the "3 of 40 tickets" (item 10, SuperBiz).** Unknown, and this agent will not invent it. Decision: count list entries (E5). Reason: the data has no quantity field, so nothing else can be counted. Risk accepted: support's earlier count may differ on repeated items. No success measure depends on it.
- **A support-facing entry point.** Decision: not in this change (Out of scope). Reason: the intent asks only for the count. A new intent is needed if it is wanted.

## Decisions for the signers at gate 2
Signing gate 2 with this text unchanged confirms:
- SuperBiz: the change is the item count and the slug is a label only; "items" means list entries; the intent's "Open questions: None" stays as signed.
- SuperDev: `item_count(order_id)` is an internal function with no `customer_id` and no route; the file list is re-checked against `docs/risk-paths` at gate 3.

## Out of scope
- Computing an order total, price, tax or any money amount.
- Item quantities, or counting by product.
- Any web route, page, JSON field or UI for the count, and any support login or role.
- Changing the order data model, `set_status`, status history, or any existing function.
- Counting items across several orders, or per customer.
- Showing the count to customers.
