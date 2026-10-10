# Spec: Order count per customer for support

References: intent.md

## Requirements
- R1: The system must return the number of orders that belong to a customer when support calls `order_count(customer_id)`. (verified by: test: C001 has 2 orders)
- R2: The system must return 0 for a customer id (a string) with no orders, without raising an error. (verified by: test)
- R3: The system must not change any order or status history when `order_count` is called. (verified by: test comparing data before and after)
- R4: The system must return only a number, never order ids, items or statuses. (verified by: test on the return type)
- R5: The system must raise `TypeError` for a customer id that is not a string. This is a new choice for this function, not an existing convention (`status_history` raises `OrderNotFound`, and `orders_for_customer(None)` returns `[]`): a support script must never show a bad id as zero orders, and `OrderNotFound` would wrongly suggest an order lookup. (verified by: test with None and 42)
- R6: `order_count` must not be reachable by customers: app/server.py and app/order_page.py must not import or call it. (verified by: test that reads both files)

## Edge cases
- E1: Unknown or empty customer id ("", "C999"): returns 0 (R2). See C1.
- E2: Malformed input (None, a number): raises TypeError (R5), so a support script cannot mistake a bad id for zero orders.
- E3: Access: support only. Customers cannot reach it (R6). The count never reveals another customer's orders; it counts only orders whose customer_id equals the argument (R1, R4).
- E4: Cancelled orders count as orders (they exist in the order list).

## Flagged concerns
- C1 (accepted risk): the sample data has no customer list, so an unknown customer id and a real customer with no orders both give 0. Support confirms the customer exists in the support tool first. A customer registry is out of scope.
- C2 (decision, for the sponsor to review): cancelled orders are counted (E4), because the question in intent.md is how many orders the customer has placed with us. The sponsor can reverse this after merge.

## Out of scope
- A customer-facing page or API endpoint.
- Counting by status.
