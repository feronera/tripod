# UX brief: Customers delete their account and data

References: intent.md

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| Delete account | Confirm and run deletion | What will be deleted; number of orders (count only) | Delete my account |
| Deleted | Tell the customer it is done | Confirmation message | Back to home |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| Delete account | No orders: still allowed; says only account data is deleted | Button disabled, "Deleting..." | Message, nothing deleted, Try again button | Go to Deleted |
| Deleted | Same as success (already deleted shows the same message) | Not needed | If sign-in is missing: go to sign-in | "Your account and data have been deleted." |

## Copy
Team language: English (no other language is set in the repo).

| key | Text | Notes |
|---|---|---|
| delete.title | Delete your account | Heading |
| delete.warning | This permanently deletes your account, your orders and their history. This cannot be undone. | Shown before the action |
| delete.empty | You have no orders. Only your account data will be deleted. | Empty state |
| delete.confirm_label | I understand this cannot be undone | Checkbox; required |
| delete.action | Delete my account | Main button, disabled until checkbox is ticked |
| delete.cancel | Keep my account | Secondary action |
| delete.loading | Deleting... | While waiting |
| delete.error | We could not delete your account. Nothing was deleted. Please try again. | Error; no ids shown |
| delete.success | Your account and data have been deleted. | Success |
| delete.home | Back to home | Link |

## Accessibility notes
- All text is readable by a screen reader, and no meaning is conveyed by color alone
- Error and success messages are announced (live region); focus moves to the message
- The checkbox has a visible label; the button works with keyboard only
- Warning text contrast at least 4.5:1; the destructive button is labeled by text, not only red
