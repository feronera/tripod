# Spec: Customers delete their account and data

References: intent.md, ux-brief.md

Code read (no ba-researcher available this run): `app/orders.py` (in-memory `_ORDERS`, `_HISTORY`, keyed by order id, owner in `customer_id`), `app/server.py` (GET-only; every other method gets 405; sign-in comes only from `identify`), `app/auth_demo.py` (demo sign-in stand-in only).

## Requirements
- R1: The system must let a signed-in customer delete their own account and personal data with one confirmed request. (verified by: test calling the delete function, then checking `orders_for_customer` is empty and `get_order` is None for their orders)
- R2: The system must delete the customer's orders and status history (`_ORDERS`, `_HISTORY`) together, so no history is left for a deleted order. (verified by: test)
- R3: The system must act only on the customer returned by `identify`, never on an id from the URL, query or body. (verified by: test with customer A signed in and customer B's id in the request; B's data is unchanged)
- R4: The system must require an explicit confirmation before deleting; a request without it deletes nothing. (verified by: test and demo)
- R5: The system must be all-or-nothing: if any step fails, nothing is deleted and the customer sees the error state. (verified by: test with an injected failure)
- R6: The system must be safe to repeat: a second delete for the same customer changes nothing and shows the same final result as success. (verified by: test)
- R7: The system must write no customer id, order id or item into logs or error text (AGENTS.md rule 6). (verified by: test capturing stderr)
- R8: The system must keep order-page behavior for other customers unchanged; existing tests in `tests/` still pass. (verified by: `make check`)
- R9: The system must use Python 3 stdlib only. (verified by: review of imports)

## Edge cases
- E1: Nobody signed in: nothing is deleted; the customer is sent to sign-in.
- E2: Customer has no orders: delete succeeds (account data only); success state shown.
- E3: Customer id malformed or not a string: treated as not found, same as `status_history`; nothing deleted.
- E4: Another customer's data is never read, changed or revealed; the response is identical whether or not other data exists.
- E5: Confirmation missing or wrong: nothing deleted; the confirm screen is shown again.
- E6: Two deletes at the same time: one deletes, the other sees "already deleted"; no error, no partial state.
- E7: Customer opens an order page after deleting: shown as not found, same as any missing order.
- E8: Wrong method (e.g. GET) on the delete path: must not delete (GET is read-only; today non-GET gets 405 in `app/server.py:50`).
- E9: Every ux-brief state (empty, loading, error, success) is reachable and tested.

## Flagged concerns
- Risk is `high` and the reasoning in intent.md is sound; no change proposed.
- Accepted risk: the repo has no real sign-in (`app/auth_demo.py` is demo only), so R3 is only as strong as `identify`. Reason: a real sign-in layer is a separate change; this change relies on the same `identify` contract as the order page.
- Accepted risk: data is in memory, so there are no backups or copies to purge here. Reason: nothing else stores customer data in this repo (checked `app/`). Real storage later must repeat this check.
- Decided: deletion is permanent, with no undo or grace period. Reason: the intent asks for deletion; a grace period would keep personal data and is a legal question for a person.
- Decided: financial or legal record retention is not handled. Reason: no such records exist in this sample; a person must decide this before any production use. Not a number or legal claim made here.
- Support-staff use (intent "Users") is covered only through the same customer flow; no staff-side delete on behalf of a customer. Reason: it would need a staff permission model that does not exist, and "read-only where possible" favors the smaller scope.
- Gate 1 was verified by `scripts/gate-check.sh` per the task; I could not re-run it in this session.

## Out of scope
- Real sign-in or session handling.
- Staff delete on behalf of a customer; bulk or admin deletion.
- Undo, grace period, export of data before deletion.
- Email or notification to the customer.
- Retention rules for legal or financial records.
