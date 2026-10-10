# Acceptance: Agent seats and agent signatures (Autonomous mode for low risk)

References: intent.md (Success measure), PR: to be opened after gate 4. Evidence: [demo/](demo/)

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Human signatures for a low-risk change in Autonomous mode: from 8 to 1 | Demo change 004 in a copy of tripod-example ([gates log](demo/004-order-count/gates-log.txt)) | Gate 1: 2 signatures by people (owner and cross, as the rule requires). Gates 2 and 3: agents only. Merge: auto-merge ALLOW. Gate 4 went to people: the agents refused it correctly (see step 5) | Partly: 2 human signatures up to merge, not 1. Gate 4 shows where autonomy stops |
| Planted defects caught 3 of 3 each | Demo change 005 ([refusals](demo/005-status-counts/)) | Spec missing an intent item: 3 of 3 refused (Opus 5.5). Plan missing a spec requirement: 3 of 3 refused (Sonnet 5.5). Every refusal names the missing item | Yes |
| Medium and high risk: 0 gates signed by agents | Tests (agent-sign refusals, gate-check rules, risk paths, governance files) | 0 | Yes |

The target of 1 human signature assumed one person signs gate 1. The rule decided at gate 1 says owner and cross are both people, so the floor is 2.

## Demo steps
1. Upgrade a copy of tripod-example to 0.8.0 with `mode: autonomous`, seats `claude-sonnet-5-5` (SuperBiz) and `claude-opus-5-5` (SuperDev), and a sponsor. A person signs gate 1 of a low-risk change (004, order count for support).
   - Expected result: gate 1 complete, Risk: low.
   - Actual result: as expected.
2. The SuperBiz agent writes spec.md; `scripts/agent-sign.sh … 2` twice.
   - Expected result: owner on Sonnet, cross on Opus, each with evidence.
   - Actual result: Opus refused 3 rounds with real findings: customers could reach the function; a bad id would look like a real 0; a cited precedent did not exist in the code. Sonnet also refused once, because the ux-brief contradicted the spec. After the fixes both approved.
3. The SuperDev agent writes plan.md; `agent-sign.sh … 3` twice.
   - Expected result: owner on Opus, cross on Sonnet.
   - Actual result: both approved first time.
4. Build, review with a read-only second opinion on Sonnet, then `auto-merge-check.sh --record`.
   - Expected result: ALLOW with agent-signed gates 2 and 3.
   - Actual result: ALLOW, after the kit update was moved to main. The first run was DENY because a kit script had been copied onto the change branch, and `scripts/` is a risk path.
5. Agents sign gate 4 after the merge.
   - Expected result: approve, or refuse with a reason.
   - Actual result: Opus refused 4 times. Tests had been edited after the lock, and `make check` failed on an older change already in the demo repo. Both are gate 4 Blockers, so the change correctly goes to a person.
6. Planted defects (change 005): a person signs owner, then `agent-sign.sh` runs the cross seat 3 times per defect.
   - Expected result: refused every time.
   - Actual result: 6 of 6 refused, each naming the missing item.

Cost of the whole demo, from activity.log: about US$2.48 (change 004 US$2.04, change 005 US$0.44).

The demo ran on the code before the review fixes (commits up to 1a5562d). The fixes make the rules stricter, for example gate 4 only after an auto-merge and governance files. Unit tests cover them; the demo was not rerun.

Disclosure: the demo repo uses invented people (Bee, Dan). The agent ran their gate 1 signatures and the planted-defect owner signatures. In real use, a person signs.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason:
- Agents signed gates 2 and 3, and auto-merge accepted the change with no person after gate 1.
- The cross-checks caught real problems and every planted defect.
- The reviews found and closed a real governance hole (B1).
- Autonomy stopped correctly at gate 4 when judgment was needed.

Open items for the PO:
- the success measure lands at 2 human signatures, not 1, because gate 1 needs owner and cross;
- the deviations listed in review.md, all of which tighten the spec.
