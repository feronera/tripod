# UX brief: Order count per customer for support

References: intent.md

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| Python call `order_count(customer_id)` in the support helper | Answer "how many orders" | One integer | Read the number |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| order_count | 0 for a customer id with no orders (an unknown id also gives 0, spec C1) | Not applicable (in-memory, immediate) | `TypeError` when the id is not a string (spec R5), so the support script shows the mistake instead of 0 | The count, for example 2 |

## Copy
| key | Text | Notes |
|---|---|---|
| none | No user-facing text | Internal function |

## Accessibility notes
- Not applicable: no user interface.
