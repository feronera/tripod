# Brief: 008-delete-account, gate 2

artifact_blob: 4d97b1bcc56817ae3065a9d1591a843c7d0f7eea
written: 2026-10-11 08:30 UTC by SuperCEO (claude-opus-5-5)

## Decision

Should people sign **gate 2** for `docs/changes/008-delete-account` (spec.md and ux-brief.md)? The change is **Risk: high**, so gate 2 needs three signatures in this order: owner SuperBiz (Bee), then cross SuperDev (Dan), then escalation (Lee). Facts: [docs/gates.md:10](docs/gates.md#L10), [docs/gates.md:44](docs/gates.md#L44), [pod.yml:3-9](pod.yml#L3-L9). Gate 1 is signed by owner and cross ([gates.log:1-2](docs/changes/008-delete-account/gates.log#L1-L2)). Gate 2 has no signatures yet.

## Options

**A. Sign gate 2 as it is (Bee, then Dan, then Lee).**
The next step is plan.md for gate 3. The spec's decisions go forward unchanged: deletion is permanent, legal record retention is not handled, and there is no staff-side delete.

**B. Send spec.md back for small edits, then sign.**
The edits would be:
- A named person takes over the two legal decisions that the agent wrote as "Decided".
- The spec defines "account data".
- intent.md risk question 3 is corrected. Editing intent.md makes the gate 1 approval stale, so gate 1 must be signed again.

After the edits, gate 2 is signed as in A. The delay is small because each edit is a few lines.

**C. Stop before gate 2 and get a legal or data-protection opinion first.**
Gate 2 waits until someone answers the retention and grace-period questions. Use this only if the pod expects the feature to go beyond this in-memory sample.

## Risks

The four risk questions are in [docs/risk-tiers.md:6-11](docs/risk-tiers.md#L6-L11).

| Question | Option A | Option B | Option C |
|---|---|---|---|
| Q1 Law or regulation | **Fact:** two decisions that touch data-protection law were written by the agent as "Decided". One is permanent deletion with no grace period ([spec.md:33](docs/changes/008-delete-account/spec.md#L33)). The other is that retention is not handled ([spec.md:34](docs/changes/008-delete-account/spec.md#L34)). The spec itself says these are "a legal question for a person". **Opinion:** if people sign without naming who owns these decisions, a legal decision gets approved without anyone owning it. | A named human takes ownership of both decisions. The small remaining risk is that the person's answer is still not legal advice. | Lowest legal risk, but the slowest option. |
| Q2 Seen by customers | **Fact:** the copy is fully specified and it promises permanence ([ux-brief.md:23](docs/changes/008-delete-account/ux-brief.md#L23), [ux-brief.md:30](docs/changes/008-delete-account/ux-brief.md#L30)). **Opinion:** the copy is acceptable. Risk from the copy is low in every option. | Same | Same |
| Q3 Rollback in minutes without data loss | **Fact:** intent.md answers "yes" ([intent.md:19](docs/changes/008-delete-account/intent.md#L19)). The spec decides deletion is permanent with no undo ([spec.md:33](docs/changes/008-delete-account/spec.md#L33)). The pod charter lists deleting data as an irreversible change ([docs/pod-charter.md:30](docs/pod-charter.md#L30)). **Opinion:** "yes" is wrong. The code can be rolled back, but deleted data cannot. The tier stays high either way. However, if gate 2 is signed now, it builds on an intent with a wrong answer, and plan.md's Rollback section may be written as if data comes back. | Correcting Q3 makes gate 1 stale ([docs/risk-tiers.md:23](docs/risk-tiers.md#L23), AGENTS.md rule 7). Gate 1 has to be signed again, which costs one extra signing round. | Same as B, plus the wait for the legal opinion. |
| Q4 Personal data | **Fact:** the only customer data in the code is `_ORDERS` and `_HISTORY` ([app/orders.py:18-35](app/orders.py#L18-L35)). Nothing in app/ stores account data. Yet R1 and E2 promise to delete "account data" ([spec.md:8](docs/changes/008-delete-account/spec.md#L8), [spec.md:20](docs/changes/008-delete-account/spec.md#L20)). **Opinion:** this is an undefined term in the requirement that matters most. The success screen could say "account deleted" when there was nothing to delete, or a later real data store could be missed. The spec does say that real storage must repeat the check ([spec.md:32](docs/changes/008-delete-account/spec.md#L32)). | The term gets defined, for example "in this repo, account data = the customer's orders and history". | Same as B |

Other facts that apply to every option:
- **R3 depends on a demo-only sign-in.** The protection against deleting another customer's data is only as strong as `identify` ([spec.md:31](docs/changes/008-delete-account/spec.md#L31), [app/server.py:48-49](app/server.py#L48-L49)). This is recorded as an accepted risk.
- **The delete route will need a method other than GET.** Today every non-GET request gets 405 ([app/server.py:50-53](app/server.py#L50-L53)). The spec only says GET must not delete (E8) and leaves the route design to plan.md. This is fine for gate 2, but SuperDev should expect it at gate 3.
- **The escalation person shares a GitHub login with SuperBiz.** In [pod.yml:13-15](pod.yml#L13-L15), `escalation_github` is the same as `superbiz_github` (`hx-natthawat`). The emails are different, so gate signing works. **Opinion:** at gate 4, CI's PR-approval check may not be able to tell Bee's approval from Lee's. That is not a gate 2 blocker.

## Evidence

- Intent and risk answers: [intent.md:14-20](docs/changes/008-delete-account/intent.md#L14-L20). The success measure "read-only where possible" is at [intent.md:12](docs/changes/008-delete-account/intent.md#L12).
- Requirements R1–R9, each with a test or demo named: [spec.md:7-16](docs/changes/008-delete-account/spec.md#L7-L16)
- Edge cases E1–E9, covering empty, invalid, access and concurrency: [spec.md:18-27](docs/changes/008-delete-account/spec.md#L18-L27)
- Flagged concerns, including the two "Decided" legal items: [spec.md:29-36](docs/changes/008-delete-account/spec.md#L29-L36)
- Out of scope: [spec.md:38-43](docs/changes/008-delete-account/spec.md#L38-L43)
- UX states: all four for both screens are at [ux-brief.md:11-15](docs/changes/008-delete-account/ux-brief.md#L11-L15). The copy is at [ux-brief.md:20-31](docs/changes/008-delete-account/ux-brief.md#L20-L31) and the accessibility notes at [ux-brief.md:33-37](docs/changes/008-delete-account/ux-brief.md#L33-L37).
- Data that actually exists: [app/orders.py:18-35](app/orders.py#L18-L35)
- Gate 2 review questions: [docs/gates.md:58-63](docs/gates.md#L58-L63). Charter rule that makes irreversible deletion high risk: [docs/pod-charter.md:26-30](docs/pod-charter.md#L26-L30)
- Signatures: [gates.log](docs/changes/008-delete-account/gates.log)
- Agent activity: [activity.log:1-19](docs/changes/008-delete-account/activity.log). One drafting run wrote spec.md and ux-brief.md, and the spec notes that no ba-researcher was used ([spec.md:5](docs/changes/008-delete-account/spec.md#L5)).
- review.md and refusals.md do not exist for this change.
- **Not verified:** I did not re-hash intent.md against the gate 1 blob. The spec also says gate 1 was not re-checked in its session ([spec.md:36](docs/changes/008-delete-account/spec.md#L36)). Someone should run `scripts/gate-check.sh docs/changes/008-delete-account 1` before signing.

## Recommendation

**Option B. People should not sign gate 2 yet.**

**Opinion:** the spec is otherwise strong. Every requirement has a test or demo, the edge cases cover access and concurrency, and all UX states and copy are present. But three things are missing or wrong:

1. **The two legal decisions need a human owner.** These are permanent deletion with no grace period, and not handling financial or legal record retention ([spec.md:33-34](docs/changes/008-delete-account/spec.md#L33-L34)). They should be restated as "accepted risk, decided by <person>", most likely Lee as escalation. The spec itself says a person must make them, and gate 2 asks whether every flagged concern has been answered or accepted.
2. **"Account data" needs a definition.** No account store exists in this repo, so R1 and E2 need to say what it means here.
3. **intent.md Q3 should be corrected to "no".** Deleted data cannot be restored within minutes. This edit makes gate 1 stale, so Bee and Dan must sign gate 1 again before gate 2 can be signed.

When these three are done and `scripts/gate-check.sh` passes for gate 1, the sign-off is Bee, then Dan, then Lee for gate 2.

Choose Option C instead only if anyone intends this flow for real customer data beyond this sample.
