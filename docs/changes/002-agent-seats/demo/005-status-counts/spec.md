# Spec: Order counts by status for support

References: intent.md

## Requirements
- R1: The system must return, for `status_counts(customer_id)`, a dict from status to the number of that customer's orders in that status. (verified by: test, C001 -> shipped 1, delivered 1)
- R4: The system must include every status in STATUS_LABELS in the result, with 0 for statuses the customer has no orders in. (verified by: test, C001 -> pending 0, paid 0, packing 0, cancelled 0)
- R2: The system must not change any order or status history. (verified by: test comparing data before and after)
- R3: The system must raise TypeError for a customer id that is not a string. (verified by: test)

## Edge cases
- E1: Unknown customer: every status with 0 (R4).
- E2: Malformed id: TypeError (R3).
- E3: Access: support only; it counts only the given customer's orders.

## Flagged concerns
- None.

## Out of scope
- A customer-facing page.
