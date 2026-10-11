# UX brief: Count the notes on an order for support

References: intent.md

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| None | Support gets the count from one call, `note_count(order_id)`, not a screen. A page is out of scope (spec.md). | A whole number | Call with an order id |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| None (call result) | Returns `0` for an order with no notes | Not applicable: in-memory call, returns at once | `OrderNotFound("Order not found")` for an unknown or malformed id | Returns the count, for example `3` |

## Copy
| key | Text | Notes |
|---|---|---|
| order.not_found | Order not found | Existing message in `app/orders.py`. Nothing new is shown to customers. |

## Accessibility notes
- All text is readable by a screen reader, and no meaning is conveyed by color alone
- No screen is added, so there are no font, contrast or keyboard changes.
