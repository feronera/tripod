# Spec: Count the notes on an order for support

References: intent.md, ux-brief.md

## Requirements
- R1: The system must provide one read-only call, `note_count(order_id)` in `app/orders.py`, that returns the number of notes on that order as an int. (verified by: unit test with an order that has 0, 1 and 3 notes)
- R2: The system must keep notes in an append-only in-memory store, like `_HISTORY` (`app/orders.py:35`), with one writer `add_note(order_id, text)`. `note_count` must never change stored notes or orders. (verified by: test that the count is the same after repeated calls and that the stored data is unchanged)
- R3: The system must raise `OrderNotFound` from `note_count` for an unknown order id, with the same message as the existing lookups (`app/orders.py:38`). (verified by: unit test)
- R4: The system must not expose `note_count` or note text through any customer route in `app/server.py`, and must not show it on the customer order page. (verified by: test that every route in `ROUTES` returns no count and no note text; demo of the order page)
- R5: The system must use only the Python 3 standard library (intent constraint). (verified by: review of imports)

## Edge cases
- E1: An existing order with no notes returns 0, not an error.
- E2: An unknown order id raises `OrderNotFound`.
- E3: A malformed id (None, int, empty string) raises `OrderNotFound` and never a `TypeError`, as `status_history` does (`app/orders.py:118`).
- E4: `add_note` with empty or whitespace-only text raises `ValueError` and stores nothing. `add_note` on an unknown order raises `OrderNotFound` and stores nothing.
- E5: One order's notes never count toward another order.
- E6: Permissions: customers can never reach the count (R4). The call has no customer id, so it is internal only; who may call it is a concern below.
- E7: UX states (see ux-brief.md): there is no screen, so empty = 0 and error = `OrderNotFound`. Loading does not apply to an in-memory call.

## Flagged concerns
- **No notes exist in the code.** `app/orders.py` has no notes field and nothing else in `app/` mentions order notes. The intent assumes support already writes notes somewhere. Decision: add a minimal in-memory store (R2) so the count can exist. Accepted risk: the real notes system may be elsewhere. Reason: nothing in the repo points to it, and a stand-in with one function is cheap to replace. SuperBiz should confirm at gate 2.
- **Risk tier may be too low.** Intent says "Personal or sensitive data: no" (`intent.md` Risk item 4). Support notes often hold personal details. The count alone is not personal, so the decision is to return only the count and never note text. Accepted risk: tier stays `low` for this change. Reason: it is read-only, internal and rolls back in minutes. Moving to real notes storage should raise the tier. I did not edit intent.md.
- **No support sign-in.** `app/auth_demo.py` only knows customers, so there is no way to check "support staff" in the app. Decision: expose a function, not a route (R4), so no new access path is created. Accepted risk: any code in the process can call it. Reason: no support identity exists to check, and adding one is a separate change.
- **"One call or page"** in the success measure: this spec picks the call. A support page is out of scope.

## Out of scope
- Any support page or HTTP route.
- Showing, searching or editing note text.
- Support sign-in and permissions.
- Persistent storage and migrating real notes.
- Notes on the customer order page.
