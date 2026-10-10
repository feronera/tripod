# Intent: Open orders per customer for support

Status: draft

## Problem
Support is asked "which of my orders are still open?" and reads the list by hand. 4 of 40 tickets last week.

## Users
Support staff, internally.

## Success measure
One call answers it: `open_orders(customer_id)` within this change. It must:
1. return the ids of the customer's orders that are not delivered or cancelled, sorted by order id;
2. return an empty list for a customer with no open orders;
3. never change any order.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers: no.
3. Rollback within minutes: yes, read-only.
4. Personal or sensitive data: no, order ids only.

## Constraints
- Python 3 stdlib only. Read-only.

## Open questions
- None.
