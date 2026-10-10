# Intent: Order count per customer for support

Status: draft

## Problem
Support staff answer "how many orders do I have with you?" by reading the order list one by one. The sample support log has this question on 6 of 40 tickets last week.

## Users
Support staff, through an internal helper. Customers do not see this directly.

## Success measure
Time to answer the question: from about 2 minutes of reading to one call, `order_count(customer_id)`, within this change.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers or external users: no. Support uses it internally.
3. Rollback within minutes without data loss: yes. It only reads data.
4. Personal or sensitive data: no. It returns a number, never order contents.

## Constraints
- Python 3 stdlib only. Read-only; must not change any order.
- A customer with no orders gets 0, not an error.

## Open questions
- None.
