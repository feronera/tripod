# Intent: Sponsor controls (budget, ceiling, automatic stops, daily digest)

Status: draft

## Problem
In Autonomous mode (0.8.0) the sponsor is on the loop but has only two levers: the kill switch and revert. Nothing limits what the agents spend or how much they change before the sponsor looks.

Evidence:
- Agent work has a real, variable cost. Change 001 cost about US$6.5 in tripod-example. The 0.8.0 demo cost US$2.48. One change 004 gate needed 4 refused agent runs before an approve. Nothing stops a loop of refusals and retries from spending without limit; the change 002 review flagged this ("no cap on agent-sign retries", review.md Minor).
- The sponsor learns about agent work only by reading PRs, gates.log and activity.log, one change at a time. There is no summary of what happened since yesterday.
- Low risk is the only limit on what agents may change. A pod cannot say "agents may not touch app/payment even at low risk" without making those paths high for people too, and cannot limit how many changes agents push through in a day.

## Users
- The sponsor in Autonomous mode: sets limits once, reads one digest a day, steps in when something stops.
- Pod members: see why an agent run was stopped and what to do.
- Teams on Pod mode: unaffected unless they set the new keys.

## Success measure
In a demo in a copy of tripod-example:
- Agent spend never exceeds the budget: with a budget per change of US$1 and per day of US$3, the run that would cross either limit is refused before it starts, and the refusal names the limit. Target: 0 runs started over budget.
- A run of refusals stops itself: after N refused agent checks on the same gate (N from pod.yml), further agent-sign runs for that gate are refused until a person acts. Target: no more than N refused runs per gate.
- The daily digest lists every agent signature, refusal, merge, revert and the spend of the last 24 hours, and matches activity.log and gates.log exactly. Target: 0 differences in the demo.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Teams that adopt Tripod get new limits on agent work.
3. Rollback within minutes without data loss: yes. Leaving the keys out of pod.yml turns the controls off.
4. Personal or sensitive data: no.

It changes governance and touches `scripts/**`, so it is high.

## Constraints
- Python 3 stdlib only; works offline. No external service is needed.
- Limits are read from pod.yml; missing keys mean no limit (today's behavior).
- Spend comes from activity.log (0.7.0), which already records every agent run's cost.
- Stopping must never cut a running session: limits are checked before an agent run starts, and the activity hook warns the agent in its session when a limit is reached.
- Pod mode keeps working as today.

## Decided (PO, 2026-10-10)
- Over budget (per change or per day): agent-sign refuses before starting, and the activity hook warns the agent, until the sponsor raises the budget. No session is cut off mid-run, and the kill switch is not set automatically.
- Daily digest: a file in the repository and a command (`scripts/digest.sh`) that prints the last 24 hours. Sending it to Slack, email or an issue is left to the team.
- Risk ceiling: limits tighter than Risk: low, set by the sponsor: how many changes agents may take to merge per day, and paths agents may not touch even at low risk (in addition to docs/risk-paths, which apply to people too).

## Open questions
- Automatic stops on repeated CI failures need GitHub data that is not in the repository. Proposal: out of scope for 003 (the digest can list failed runs later), keep stops on budget, refusals in a row, and a revert in the last 24 hours. PO to confirm.
