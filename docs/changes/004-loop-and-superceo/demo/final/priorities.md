# Priorities, 2026-10-11 11:51 UTC (SuperCEO, claude-opus-5-5)

1. **006-order-status-label**: all 4 gates signed, Risk low; next step: merge (`/superdev:merge`, so `auto-merge-check` decides between ALLOW and a person merging, then SuperBiz accepts within 48 h); blocker: someone has to approve or run the merge; spend US$2.73; reason: finished, cheaper than 004, and it removes 4 of 40 tickets.
2. **004-order-total**: all 4 gates signed, Risk low; next step: merge (`/superdev:merge`, same path as 006); blocker: someone has to approve or run the merge; spend US$4.75; reason: finished and fixes 3 of 40 tickets, but it has the highest spend so far and saves slightly fewer tickets than 006.
3. **005-refund-note**: gate 1 signed, Risk high; next step: spec, then gate 2 signed by the owner, the cross-checker and the escalation signer; blocker: needs people (high risk needs the extra escalation signature at gates 2 and 4); spend US$0.41; reason: biggest win (6 of 40 tickets, target 2 per week) for little spend so far, but it is far from done.
4. **007-order-note-count**: gates 1–3 signed, Risk low; next step: build and review, then gate 4; blocker: the intent has no named call or concrete rules ("one call or page does it"), so it's unclear what gate 4 should accept; spend US$0.75; reason: close to done but the value is unclear (3 of 40 tickets); sharpen the intent before more spend.
5. **008-delete-account**: gate 1 signed, Risk high; next step: the sponsor rewrites the intent with a concrete problem and success measure; blocker: the intent is a placeholder, and "read-only where possible" doesn't fit deleting accounts, which is destructive and can't be undone; spend US$0.14; reason: unclear value (3 of 40 tickets) with the highest risk; hold until the intent is fixed.
6. **001-order-history**: passed gate 4 and on main, Risk high; next step: none; blocker: none; spend US$0.00; reason: done.
7. **002-status-report**: passed gate 4 and on main, Risk low; next step: none; blocker: none; spend US$0.00; reason: done.
8. **003-order-page**: passed gate 4 and on main, Risk high; next step: none; blocker: none; spend US$0.00; reason: done.

Backlog: none (there is no `docs/backlog.md`).

Changes 004–008 are on branches that aren't checked out, so I couldn't read their intent.md, gates.log or activity.log. For those, the states, spend and intents above come from the summary you gave me, not from the logs.
