# UX brief: Sponsor controls

References: intent.md

The users are the sponsor (sets limits, reads the digest, resumes), pod members, and the agents (they see refusals and the in-session warning). Plain text in a terminal, CI logs and a Markdown file.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/agent-sign.sh` refusal (new reasons) | Stop agent work at a limit before it costs money | which limit, spend, estimate, how to lift it | Wait for the sponsor |
| Hook message in the agent's session | Tell the agent early, once | limit reached, what will be refused | Stop starting new checks; hand over |
| `scripts/resume.sh <dir> "<reason>"` | A person lets agents try again after repeated refusals | the recorded line | Resume |
| `scripts/digest.sh [--hours N] [--write]` | The sponsor's daily view | spend, signatures, refusals, merges, reverts, resumes, stops, limits | Read; adjust limits; revert |
| `auto-merge-check` DENY (new reasons) | Keep the ceiling at merge | forbidden path, merges today | People merge |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| digest | Each section says `nothing in the last 24 hours`; spend `US$0.00` | Not applicable | Malformed pod.yml limit: `pod.yml: budget_per_day_usd: abc is not a number`, exit 1 | The full digest (below) |
| agent-sign | Not applicable | Unchanged (`Checking gate …`) | The refusal copy below, exit 1 | Unchanged |
| resume | Not applicable | Not applicable | `Refused: git email 'x' is not the sponsor or a member in pod.yml`, exit 1 | `Resumed: 004-x (agent checks may run again on every gate)` |

Digest example:
```
Tripod digest, last 24 hours (2026-10-09 06:00 → 2026-10-10 06:00 UTC)
spend: US$4.12 (limit US$5.00 per day) · unknown: 0 records
  004-order-count  US$3.20  (claude-opus-5-5 US$1.90, claude-sonnet-5-5 US$1.30)
  005-status-counts US$0.92
agent signatures: 004-order-count gate 2 owner claude-sonnet-5-5, gate 2 cross claude-opus-5-5
refused agent checks: 004-order-count 4 (gate 2: 3, gate 4: 1)
auto-merges: 004-order-count at 2026-10-10 01:39
reverts: nothing in the last 24 hours
resumes: nothing in the last 24 hours
stops in force: 005-status-counts gate 2: 3 refusals in a row (max_refusals_per_gate: 3); resume with scripts/resume.sh
limits: budget_per_change_usd 2.00, budget_per_day_usd 5.00, max_refusals_per_gate 3, agent_merges_per_day 2, agent_forbidden_paths app/payment*
```

## Copy
| key | Text | Notes |
|---|---|---|
| budget_change | Refused: budget for {change} reached: spent US${spent} of US${limit} (budget_per_change_usd), and the next check may cost about US${estimate}. The sponsor can raise the limit in pod.yml | agent-sign |
| budget_day | Refused: today's budget reached: spent US${spent} in the last 24 hours of US${limit} (budget_per_day_usd), next check about US${estimate}. The sponsor can raise the limit in pod.yml | agent-sign |
| refusals | Refused: gate {n} has {count} refused agent checks since a person last acted (max_refusals_per_gate: {max}). A person reviews it, then runs scripts/resume.sh {dir} "<reason>" | agent-sign |
| revert | Refused: {change} was reverted at {time}; agents pause for 24 hours after a revert (until {until}) | agent-sign |
| forbidden | Refused: this change touches {paths}, which agents may not change (agent_forbidden_paths); people sign it | agent-sign and auto-merge DENY (adapted) |
| merges_today | {count} changes were auto-merged in the last 24 hours (agent_merges_per_day: {max}); people merge this one | auto-merge DENY |
| hook_warning | Tripod: the {which} budget is reached (US${spent} of US${limit}). scripts/agent-sign.sh will refuse until the sponsor raises it. Finish the current step and hand over | in the agent's context, once per session per limit |
| resumed | Resumed: {change} (agent checks may run again on every gate) | resume.sh |
| nothing | nothing in the last {hours} hours | digest |

## Accessibility notes
- Plain text; amounts always with `US$` and two decimals; times in UTC with the date.
- Every refusal says who can lift it and how.
