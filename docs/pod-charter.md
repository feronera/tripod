# Pod charter

Fill in this document together before the first change, and review it whenever the members change.

## Members
A role can have several people: add one row per person (pod.yml lists them comma-separated, in the same order).

| Role | Name | Email (matches pod.yml) | Responsible for |
|---|---|---|---|
| SuperBiz | | | PO, PM, BA, Designer: what to build and why |
| SuperDev | | | SA, Dev, QA, Deploy, Maintenance: how to build it, and whether it is safe |
| Escalation | | | Additional signature at gates 2 and 4 for Risk: high changes |

## Who reviews whom
- SuperBiz cross-checks SuperDev's gates (3 and 4), and SuperDev cross-checks SuperBiz's gates (1 and 2). Any member of the role may sign.
- With 2 or more SuperDevs: the gate 4 owner, and the SuperDev who approves the PR, is a SuperDev who did not write the code. Default reviewer pairs: <e.g. Dan reviews Eve, Eve reviews Dan>
- With more than one SuperBiz: who signs gates 1 and 2 for which product area: <...>
- Keep to about 3 SuperDevs per SuperBiz. Review this section when members change (see `docs/scaling.md`).

## Working hours
- Hours when both people are reachable:
- Main communication channel:
- Expected response time for cross-check requests:

## Backup people and escalation
- Backup person when SuperBiz is away:
- Backup person when SuperDev is away:
- When the two disagree at a gate, the decision is made by:

## WIP limit
- Number of changes that may be open at once: 2 (matches `wip_limit` in pod.yml). The limit is pod-wide; start with 2 per SuperDev, capped by what SuperBiz can review
- An open change is one that has passed gate 1 but not yet gate 4.

## What the pod may not do alone (must be Risk: high with escalation)
- Change how personal data is stored or displayed
- Change how money, prices or taxes are calculated
- Change access permissions or authentication
- Make irreversible changes, such as deleting data or an irreversible migration
- <additional items for your team>

## Rules belong in the structure
- A rule broken twice must move from a skill into a hook, script or CI check.
- Record each move here: <date, rule, what it became>

## Auto-merge trust ladder
| Step | `auto_merge` in pod.yml | Condition |
|---|---|---|
| 1 | `off` | Default. Every change needs a human signature before merge |
| 2 | `low` | The pod has closed `auto_merge_min_track` consecutive changes without a revert, and both people agree to enable it |
| Back to step 1 | (automatic) | A revert within the last `auto_merge_min_track` changes makes auto-merge-check DENY until a new track record is built |

- Medium and high changes are never merged automatically, at any step.
- Who may change `auto_merge`: <name> (pod.yml is in docs/risk-paths, so the change requires escalation)

## Kill switch
- Who may turn it on: both people (`touch .pod/kill-switch`)
- Who may turn it off: the person who turned it on, after investigating the cause (`rm .pod/kill-switch`)
