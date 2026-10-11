# UX brief: Status label lookup for support

References: intent.md

## Screens
None. This is a function called from support scripts. No page, form or customer-visible change.

## States
- Success: known code returns the customer wording, e.g. "Preparing order".
- Not found / malformed: returns the text "Unknown status". No error, no empty value.
- Loading and error: not applicable (in-memory lookup, never raises).

## Copy
- "Unknown status" (English, exactly this text; the labels in `STATUS_LABELS` are the team's existing wording, unchanged).

## Accessibility
Not applicable: no interface. Output is plain text, so scripts can print it as is.
