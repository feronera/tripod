# Spec: Open orders per customer for support

References: intent.md

## Requirements
- R1: The system must return, for `open_orders(customer_id)`, the ids of that customer's orders. (verified by: test, C001 -> A1001, A1002)
- R2: The system must not change any order. (verified by: test)

## Edge cases
- E1: Unknown customer: an empty list.

## Flagged concerns
- None.

## Out of scope
- A customer-facing page.
