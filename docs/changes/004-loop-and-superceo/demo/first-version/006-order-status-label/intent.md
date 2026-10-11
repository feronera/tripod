# Intent: Status label lookup for support

Status: draft

## Problem
Support scripts print raw status codes ("packing") and staff translate them to the customer wording by hand. 4 of 40 tickets last week quoted a raw code.

## Users
Support staff, internally. Customers do not see it.

## Success measure
One call gives the customer wording: `status_label(code)` within this change. It must:
1. return the label from STATUS_LABELS for a known code;
2. return "Unknown status" for any other value, without raising;
3. never change any order.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers: no.
3. Rollback within minutes: yes, read-only.
4. Personal or sensitive data: no.

## Constraints
- Python 3 stdlib only.

## Open questions
- None.
