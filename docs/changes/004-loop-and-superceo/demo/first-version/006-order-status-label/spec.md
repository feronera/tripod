# Spec: Status label lookup for support

References: intent.md, ux-brief.md

## Requirements
- R1: The system must return the label from `STATUS_LABELS` (`app/orders.py:9`) when given a known status code, e.g. "packing" gives "Preparing order". (verified by: unit test over every key in `STATUS_LABELS`)
- R2: The system must return the text "Unknown status" for any value that is not a key of `STATUS_LABELS`, and must not raise. (verified by: unit test)
- R3: The system must not change any order, status history or `STATUS_LABELS` when the lookup is called. (verified by: unit test comparing orders and history before and after a call)
- R4: The system must keep the behavior of the existing `status_label` unchanged (it returns the raw code for unknown values), so the customer page and `status_counts` do not change. (verified by: existing tests in `tests/test_orders.py` and `tests/` for the order page still pass)

## Edge cases
- E1: Empty string, None, number, list or dict as the code: return "Unknown status", no exception (a list or dict is unhashable, so the lookup must guard it).
- E2: Wrong case or surrounding spaces ("Packing", " packing "): "Unknown status". Decision: exact match only, because the intent says "known code" and guessing could show a wrong label to a customer through support.
- E3: A code that is a label text ("Shipped"): "Unknown status".
- E4: No permissions case: the function takes a code only and reads no order or customer data, so no user data can leak.

## Flagged concerns
- `status_label` already exists in `app/orders.py:72` and returns the raw code for unknown values (used by `status_for_customer`, `status_history`, `status_counts`). Intent asks for "Unknown status" under the same name. Changing it would show "Unknown status" on the customer page and change the keys of `status_counts`, which breaks R4. Decision: add a separate support function and leave the old one alone; the exact name is for SuperDev to choose in plan.md. SuperBiz should confirm that the intent wording `status_label(code)` is satisfied by a differently named function. Accepted risk: two similar functions may confuse readers; the docstrings must say which is for support.
- Risk stays low: read-only, no personal data, not seen by customers. No sensitive paths touched found by this spec.
- ux-brief.md: no screen. Support calls it from scripts, so it only states the text. 

## Out of scope
- Changing the customer order page or `status_counts`.
- Translating labels into other languages, or adding new status codes.
- Changing support scripts to use the function (follow-up).
- Trimming, case-folding or guessing near-matches of codes.
