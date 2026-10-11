# Intent: Item count per order for support

Status: draft

## Problem
Support is asked "how many items are in my order?" and counts the item list by hand. 3 of 40 tickets last week.

## Users
Support staff, internally. Customers do not see it.

## Success measure
One call answers it: `item_count(order_id)` within this change. It must:
1. return the number of items in an existing order;
2. raise OrderNotFound for an order that does not exist, like the other lookups;
3. never change any order.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers: no.
3. Rollback within minutes: yes, read-only.
4. Personal or sensitive data: no, a count only.

## Constraints
- Python 3 stdlib only. Read-only.

## Open questions
- None.
