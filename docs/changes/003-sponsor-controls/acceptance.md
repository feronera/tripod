# Acceptance: Sponsor controls (budget, ceiling, automatic stops, daily digest)

References: intent.md (Success measure), PR: to be opened after gate 4. Evidence: [demo/](demo/)

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| 0 agent runs started over budget | Demo: change budget US$0.15, spend US$0.13 ([budget-stop](demo/budget-stop.txt)) | Refused before any agent started: US$0.13 spent, next run about US$0.34 | Yes |
| No more than N refused runs per gate | Demo: `max_refusals_per_gate: 2` with a planted defect ([run1](demo/run1.txt), [run2](demo/run2.txt), [run3](demo/run3.txt)) | Two real refusals by Opus 5.5 naming the missing intent items; the third attempt refused before starting | Yes |
| The digest matches the logs exactly | [digest](demo/digest.txt) against an independent sum of every activity.log ([004](demo/activity-log-004.txt), [005](demo/activity-log.txt)) | US$2.39 in the digest and in the independent sum, 0 unknown. The refusals, the resume and the auto-merge match the logs | Yes |

## Demo steps
Run in a copy of tripod-example on 0.9.0 with the real `claude`. The limits changed during the demo, by the sponsor on main: per-change budget US$1.20, then US$0.15, then US$0.10; `max_refusals_per_gate: 2`; `agent_forbidden_paths: app/billing*`.
1. A person signs gate 1 and the gate 2 owner of change 005 (a spec that drops the "open" filter). `agent-sign.sh … 2` three times.
   - Expected result: two refusals, then a stop.
   - Actual result: as expected ([gates log](demo/gates-log.txt), refused checks: 2).
2. The sponsor runs `resume.sh` and lowers the budget to US$0.15; `agent-sign.sh … 2`.
   - Expected result: refused over budget.
   - Actual result: "spent US$0.13 of US$0.15 … next check may cost about US$0.34".
3. With the budget at US$0.10 (already reached), a real Claude Code session runs with the superdev plugin.
   - Expected result: the warning reaches the agent.
   - Actual result: the agent quoted "Tripod: the change budget is reached (US$0.13 of US$0.10) …" and stopped without changing anything ([session](demo/hook-warning-session.txt)).
4. `app/billing.py` is added; `agent-sign.sh … 2`.
   - Expected result: refused, forbidden path.
   - Actual result: as expected ([forbidden-stop](demo/forbidden-stop.txt)).
5. `scripts/digest.sh`.
   - Expected result: totals equal to the logs, and the stops in force listed.
   - Actual result: as expected. This step found that per-change budget stops were missing from "stops in force"; they were fixed before review.

Cost of the demo: about US$0.34 in agent runs (change 005).

The demo ran before the review fixes. They make the rules stricter (the clock, base-branch logs, identities, amounts); unit tests cover them and the demo was not rerun. The demo repo uses invented people; the agent ran their signatures and the sponsor's resume. In real use, people do.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason:
- Every control worked with the real claude: the budget stop, the refusal stop and resume, the warning in the agent's session, the forbidden path, and the digest.
- The digest matched the logs exactly.
- The review closed a real bypass (B1) and the gaps around it.

Open item for the PO: the limits listed in docs/autonomous.md under "Limits you accept" (parallel starts, unmerged branches, failed runs, the warning in people's sessions).
