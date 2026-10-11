# Spec: Refund note on cancelled orders

References: intent.md, ux-brief.md

## Requirements
- R1: The system must show one refund note on the order page of an order whose current status is `cancelled`. (verified by: test that renders a cancelled order and finds the note once, using order A1004 in `app/orders.py`)
- R2: The system must not show the refund note on an order in any other status (`pending`, `paid`, `packing`, `shipped`, `delivered`). (verified by: test over every status code in `app/orders.py` that only `cancelled` shows the note)
- R3: The system must decide whether to show the note from the order's current status, not from the history rows. (verified by: test where history is empty and the status is `cancelled`, and a test where the history contains a cancelled row but the current status is another one)
- R4: The system must place the note in the "Current status" section, below the status label and "Updated" line and above "Status history" (ux-brief.md "Layout"). (verified by: test on rendered HTML order of elements)
- R5: The system must take the note text from one entry in `COPY` (`refund.note`) in `app/order_page.py`, in the wording approved by legal, exactly as written in ux-brief.md "Copy". (verified by: test that the page text equals the `COPY` entry, and demo of the legal approval record)
- R6: The system must not show the note until legal has approved the wording, and the change must not be released before then. (verified by: release-check evidence that legal approval is recorded in acceptance.md or runbook.md; this is a human check, not a unit test)
- R7: The system must escape the note text the same way as all other order page text. (verified by: existing escaping test pattern in `tests/test_order_page.py` applied to the note)
- R8: The system must show the note on the same pages that already show an order, including the page swapped in after loading from `/content/orders/{id}`, with the same text in both. (verified by: server test on the full page and on the content route, `tests/test_order_server.py`)
- R9: The system must keep every other part of the order page unchanged for all statuses and states: not found, load error, signed out, loading and empty history. (verified by: the existing tests in `tests/test_order_page.py`, `tests/test_order_server.py` and `tests/test_order_history.py` pass without edits)
- R10: The system must not add personal data, amounts, dates or payment details to the note. The note is the same text for every cancelled order. (verified by: test that two different cancelled orders render the same note text)
- R11: The system must make the refund note something the team can switch off without changing the status display, so a wording problem found after release can be rolled back within minutes (intent.md Risk answer 3). (verified by: demo of the rollback step in runbook.md; the mechanism is SuperDev's decision in plan.md)

## Edge cases
- E1: Cancelled order with no history rows (Empty view): the note is still shown. (see R3)
- E2: Cancelled order whose latest history row is not the current status (the "Updated" line is hidden, see `Success.updated` in `app/order_page.py`): the note is still shown, under the status label.
- E3: An order that was cancelled and later moves to another status, if the data allows it: the note is not shown, because only the current status counts (R2, R3).
- E4: Order not found, another customer's order, or a malformed id: the existing "Order not found" page is shown with no note and nothing about the order (existing R7 of change 003).
- E5: Load error or signed-out customer: the existing error or redirect is shown, no note (R9).
- E6: Unknown status code that has no label: no note is shown, and existing behavior is unchanged.
- E7: A cancelled order of one customer must never make the note appear on, or be inferred from, another customer's order page. The note carries no per-order data (R10), so it cannot leak any.
- E8: Loading state: the shell shows no note. The note appears only with the loaded order (ux-brief.md States).
- E9: The note text contains characters that need escaping (for example `&` or an apostrophe): they appear correctly to the customer and cannot inject markup (R7).

## Flagged concerns
- **Risk is high and is correctly stated.** intent.md declares `Risk: high`; this spec agrees. A refund statement is a consumer-law promise. Gates 2 and 4 therefore need the escalation signature from `pod.yml` (`docs/risk-tiers.md`). Under `docs/merge-by-risk.md` a human merges. No change to intent.md is needed.
- **Wording is not written and is not ours to write.** The `refund.note` text in ux-brief.md is a placeholder. intent.md says legal must approve it before release. No test or code should hold invented refund wording as final. SuperBiz must obtain the text and the approval, and record where the approval is kept (see Open questions).
- **Facts the note depends on are unknown.** intent.md says only "refund note"; it does not say whether every cancelled order is refunded. `app/orders.py` has an order that went `pending` and may be cancelled before payment, where no refund is due, yet the note would show for every `cancelled` order. A note that promises a refund to a customer who paid nothing is the kind of statement legal must see. SuperBiz and legal must decide whether one note fits all cancelled orders or whether the status data needs a "was it paid" signal. The second option would be a bigger change (see Out of scope).
- **The view does not carry the raw status.** In `app/order_page.py`, `resolve` returns `Success` and `Empty` with only the label (`"Cancelled"`), not the status code, although the loaded record has both (see `tests/test_order_history.py` E12). Showing the note needs the code or a label match. SuperDev should decide this in plan.md. It is an implementation concern, noted here so R1 to R3 are not satisfied by matching the display label text.
- **Existing tests may assert the exact page content of cancelled orders.** `tests/test_order_page.py` (around lines 490 to 503) and `tests/test_order_history.py` (E12) use cancelled orders. If any compare the full cancelled page, they will fail by design when the note is added, and tests in `tests/` can be locked (`.pod/lock-tests`). SuperDev must say which tests need updating, and a human must do it if the lock is on.
- **Success measure is partly outside the product.** "Refund questions in tickets drop from 6 to 2 per week within a month" is measured from support tickets, not from the app. This change can only show the note. Who measures it, and how tickets are counted, are not stated. The baseline "6 of 40 tickets last week" is taken from intent.md and has not been checked.
- **Placement is a proposal.** The position under the status label (ux-brief.md "Layout") is a design choice for SuperBiz to confirm.
- **Language and region.** The page copy is English and the page states times in Bangkok time. Which consumer law applies, and whether the note needs another language, are unknown (see Open questions).
- **Tool limits in this run.** The `ba-researcher` agent and `scripts/gate-check.sh docs/changes/005-refund-note 1` could not be run in this session (no shell access). Gate 1 was checked only by reading `gates.log`: it shows both owner and cross entries for the intent blob. Code impact comes from reading `app/order_page.py`, `app/orders.py`, `docs/risk-paths` and searching the tests. A human or the next step should run the gate-1 check.

## Out of scope
- Starting, calculating, tracking or showing the status of an actual refund.
- Any amount, date, payment method or reference number on the note.
- Changing how or when an order becomes `cancelled`, or adding a "paid before cancel" field to orders.
- Emails, notifications or a support-ticket link triggered by cancellation.
- Changes to the order history list, status labels or timezone note.
- Any change to sign-in, access rules or payment code (`app/auth*`, `app/payment*`), which would also raise the risk path (`docs/risk-paths`).
- Translating the page or adding languages.
- Building the support-ticket measurement of the success measure.

## Open questions
- What exact wording does legal approve for `refund.note`, who at legal approves it, and where is the approval recorded?
- Is every cancelled order refunded? What about orders cancelled before payment?
- Is there a refund time or method the note may state, and if so what is it? (Not invented here.)
- What should the customer do if the refund does not arrive: contact `support@shop.example` or something else?
- Which consumer law and region apply to this statement?
- Who measures the ticket numbers for the success measure, and from which tool?
- Is the note's position under the status label accepted?
