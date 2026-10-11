# Brief: 005-refund-note, gate 2

artifact_blob: c8acbc920a97ce2e4c36841196058f3f82d28b50
written: 2026-10-11 03:32 UTC by SuperCEO (claude-opus-5-5)

# Brief: 005-refund-note at gate 2 (spec.md + ux-brief.md)

Risk: high · Branch `change/005-refund-note` · 2026-10-11 · read-only, nothing signed

## Decision
Should gate 2 be signed for spec.md and ux-brief.md now? Because Risk is high, gate 2 needs three signatures, in this order:
1. Owner: Bee (SuperBiz)
2. Cross: Dan (SuperDev)
3. Escalation: Lee

Gate 1 is complete in `gates.log`. Gate 2 has no signatures yet.

The real question is whether the spec is solid enough to sign while two facts are still unknown:
- **The wording.** The `refund.note` text is a placeholder: "TO BE WRITTEN AND APPROVED BY LEGAL".
- **Whether every cancelled order is refunded.** Some orders may be cancelled before payment.

## Options
1. **Sign now and accept the open questions as risks.** The spec already protects release: R6 says nothing ships until legal approves, and R5 requires the exact approved text. Plan.md can start sooner. The cost is that legal's wording will change ux-brief.md, and possibly R1/R2. Any edit to a signed artifact makes the approval stale, so the people would very likely sign gate 2 again, including Lee.
2. **Hold, answer the blocking questions, revise, then sign (recommended).** SuperBiz gets two answers first:
   - Does the note apply to orders cancelled before payment?
   - Who at legal approves the wording, and where is the approval recorded?

   SuperBiz also confirms where the note sits on the page. The agent then revises spec.md, and all three people sign once. It is slower at the start but avoids signing twice.
3. **Narrow the scope.** Show the note only where a refund is certain. This needs a "paid before cancel" signal, which the spec puts out of scope. It is a bigger change and might need a new or amended intent, and changing intent.md would make the gate 1 signatures stale too.

## Risks
- **The note could promise money to customers who paid nothing.** R1/R2 show the note on *every* `cancelled` order, but `app/orders.py` has orders that can be cancelled while still `pending`. Under consumer law that is a false promise. This is the main reason not to sign as written.
- **Signatures will likely go stale.** The final legal wording goes into ux-brief.md "Copy", and possibly into R1/R2. If gate 2 is signed first, Bee, Dan and Lee will likely have to sign again.
- **Some facts are unknown.** These include which law and region apply, whether the note can state a refund time or method, the support contact, and who measures the ticket drop. None are invented in the spec, but each needs an owner.
- **Existing tests may break by design.** Tests that check the whole page for cancelled orders (`tests/test_order_page.py` around lines 490–503, `tests/test_order_history.py` E12) may fail once the note is added. `.pod/lock-tests` doesn't exist right now. If it is turned on before plan.md, a human has to update those tests.
- **Gate 1 was never checked by script.** The spec drafter had no shell (spec.md "Tool limits"). Both gate 1 lines are timestamped the same second (`10:25:01+07:00`), which is worth confirming with `scripts/gate-check.sh docs/changes/005-refund-note 1`.
- **The WIP limit may be exceeded.** `wip_limit: 2`, and 003, 004 and 005 may all count as open, depending on 003's gate 4 state. A human should check before this change moves on.
- **Spend is low.** US$0.41 so far, for one spec-drafting step, out of the US$8.00 per-change budget.

## Evidence
- [intent.md](docs/changes/005-refund-note/intent.md): Risk high (Q1 law: yes; Q2 seen by customers: yes; Q3 rollback in minutes: yes; Q4 personal data: no); constraint that legal approves before release
- [spec.md](docs/changes/005-refund-note/spec.md): R1–R11, E1–E9, Flagged concerns, 7 Open questions
- [ux-brief.md](docs/changes/005-refund-note/ux-brief.md): note placement, all 4 states covered, copy placeholder
- [gates.log](docs/changes/005-refund-note/gates.log): gate 1 owner and cross signatures, no gate 2 entries
- [activity.log](docs/changes/005-refund-note/activity.log): loop run `20261011T032848`, step "draft spec", result ok, US$0.408212
- [docs/gates.md](docs/gates.md) and [docs/risk-tiers.md](docs/risk-tiers.md): escalation required at gates 2 and 4; editing an artifact makes its approval stale
- [pod.yml](pod.yml): signers, `wip_limit`, `budget_per_change_usd`
- [docs/superceo/2026-10-11.md](docs/superceo/2026-10-11.md): today's priorities put 005 below 003

## Recommendation
**Option 2: don't sign gate 2 yet.**
1. **SuperBiz (Bee)** answers the two blocking questions (cancelled-before-payment orders; legal approver and where the approval is recorded) and confirms the note's position.
2. **The agent** revises spec.md, and ux-brief.md if needed, from those answers. The other open questions (refund time or method, law and region, ticket measurement) are accepted as named risks, each with an owner.
3. **SuperDev (Dan)** runs `scripts/gate-check.sh docs/changes/005-refund-note 1` and checks the WIP count.
4. **Then the three people sign gate 2:** Bee, then Dan, then Lee.

Option 1 is reasonable only if legal can give the final wording before plan.md is drafted. Otherwise expect to sign gate 2 twice.

---

- **The brief is only in this message, not saved.** `docs/autonomous.md` says it belongs in `docs/changes/005-refund-note/brief.md`, but I had no tool to write files this session. Save it there if you want to keep it.
- **I couldn't find the `/superceo:brief` skill file**, so I followed the brief format in `docs/autonomous.md`.
- **Nothing was signed**, and I didn't touch `gates.log` or any scripts.
