# Acceptance: Order count per customer for support

References: intent.md (Success measure), merged locally with an auto-merge record

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Support answers "how many orders" with one call | Run order_count on the sample data | C001 2 C003 1 C999 0 | Yes |

## Demo steps
1. Call order_count("C001").
   - Expected result: 2
   - Actual result: 2
2. Call order_count("C003") (one cancelled order).
   - Expected result: 1 (cancelled orders count, spec C2)
   - Actual result: 1
3. Call order_count("C999") and order_count(None).
   - Expected result: 0, then TypeError
   - Actual result: 0, then TypeError (None -> TypeError: customer_id must be a string)

## Decision
Decision: accept

Reason: every requirement R1-R6 is met in the demo and by tests; the two accepted decisions (spec C1 and C2) are listed for the sponsor.
