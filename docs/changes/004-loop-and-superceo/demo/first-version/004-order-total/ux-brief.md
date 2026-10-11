# UX brief: Item count per order for support

References: intent.md

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| None | This change adds only a function, `item_count(order_id)`, for internal use. No screen, page or message is added or changed. | Not applicable | Not applicable |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| None | Not applicable. An order with no items returns 0 to the caller. | Not applicable. The lookup is in memory and has no waiting state. | The caller gets `OrderNotFound("Order not found")`, the same message the other lookups use. No UI shows it. | The caller gets an integer. |

## Copy
| key | Text | Notes |
|---|---|---|
| order_not_found | Order not found | Existing exception message in `app/orders.py`. No new user-facing text is added. |

## Accessibility notes
- All text is readable by a screen reader, and no meaning is conveyed by color alone
- No screen is added, so there are no font, contrast or keyboard changes.
- If a later change shows the count on a page, it needs its own ux-brief.
