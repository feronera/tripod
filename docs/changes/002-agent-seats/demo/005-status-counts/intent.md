# Intent: Order counts by status for support

Status: draft

## Problem
Support staff are asked "which of my orders are still on the way?" and count statuses by hand. 5 of 40 tickets last week.

## Users
Support staff, internally. Customers do not see it.

## Success measure
One call answers it: `status_counts(customer_id)` returns a count for every status, within this change. It must:
1. count a customer's orders per status;
2. include every status in STATUS_LABELS, with 0 for statuses the customer has no orders in;
3. never change any order.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers or external users: no.
3. Rollback within minutes without data loss: yes, read-only.
4. Personal or sensitive data: no, counts only.

## Constraints
- Python 3 stdlib only. Read-only.

## Open questions
- None.
