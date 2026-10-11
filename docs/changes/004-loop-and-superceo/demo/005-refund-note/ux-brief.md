# UX brief: Refund note on cancelled orders

References: intent.md

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| Order page (existing, change 003), cancelled order only | Tell the customer, without contacting support, what happens about their money after cancellation | Current status "Cancelled", the refund note, then the existing status history | Read the note; none new |

No new screen. The note is one block on the existing order page, shown only when the order's current status is `cancelled`. Orders in any other status look exactly as they do today.

### Layout
- The note sits in the "Current status" section, directly under the status label and the "Updated" line, above "Status history". This is the first place a customer looks after seeing "Cancelled".
- It is plain text in a paragraph, with no dialog, banner or link that must be followed.
- Position is a proposal for SuperBiz to confirm (see spec Flagged concerns).

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| Order page, cancelled order | Order has no history rows: the note is still shown, because it depends on the current status, not on history | Existing loading shell. The note is not shown until the order has loaded, and no placeholder note is shown | Existing "Order not found" and "We couldn't load your order" screens are unchanged and never show the refund note | Status "Cancelled" followed by the refund note |
| Order page, any non-cancelled order | Unchanged | Unchanged | Unchanged | Unchanged, no refund note |

## Copy
| key | Text | Notes |
|---|---|---|
| refund.note | TO BE WRITTEN AND APPROVED BY LEGAL | Not drafted by this pod. It is a promise under consumer law (intent.md Risk, Constraints). The words must not go into the code or tests as final until legal approves. |

Copy facts the wording must settle, taken from the open questions in spec.md: whether a refund is always given, how long it takes, to which payment method, what a customer should do if it does not arrive, and what to say if the order was cancelled before it was paid.

Language: English, the language of the existing order page copy (`COPY` in `app/order_page.py`).

## Accessibility notes
- All text is readable by a screen reader, and no meaning is conveyed by color alone
- The note is ordinary paragraph text inside the "Current status" section, so a screen reader reads it right after the status. It is not a live region, because it is not a change announced after load.
- Same font size and text/background contrast as the surrounding status text; no smaller "fine print" style, so the promise is as readable as the status.
- Nothing in the note needs a mouse or a keyboard action.
