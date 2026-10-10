# UX brief: Loop driver and the SuperCEO agent

References: intent.md

The users are the sponsor (turns the loop on, reads what it did, decides briefs), pod members (sign gate 1 and every medium or high gate) and CI. Plain text in a terminal and CI logs; Markdown for priorities and briefs.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/loop.sh` | One loop run | per change: the step taken, its result, why it stopped; a summary line | Read; act where people are needed |
| `scripts/loop.sh --dry-run` | See what a run would do | per change: next step and who acts | Decide whether to run |
| `scripts/superceo.sh priorities` → `docs/superceo/YYYY-MM-DD.md` | The sponsor's ranked view | rank, change, state, next step, blocker, spend, reason | Reorder or unblock work |
| `scripts/superceo.sh brief <dir>` → `brief.md` | Prepare a high-risk decision | decision, options, risks, evidence links, recommendation | Sign or refuse the gate |
| digest section `loop runs` | Daily summary of the loop | steps and stops by reason | Read |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| loop.sh | `Loop: nothing to do (no open changes past gate 1)` | `Loop run 2026-10-10 14:00 UTC: 005-open-orders: drafting spec.md (agent:superbiz, claude-sonnet-5-5)...` | Refused to start (copy below), or per change: `005-open-orders: stopped: <reason>` | `005-open-orders: draft spec → done; sign gate 2 owner → APPROVE; …` then `Loop run: 4 steps, 1 stop (005-open-orders: people sign gate 2)` |
| dry-run | Same as empty | Not applicable | Same refusals | `005-open-orders (low): next: draft spec.md (agent:superbiz)` per change |
| priorities | `No open changes and no docs/backlog.md: nothing to rank` | `Ranking with claude-opus-5-5...` | `superceo: claude did not return a ranking (<reason>). Nothing was written` | `Wrote docs/superceo/2026-10-10.md (3 changes, 2 backlog items)` |
| brief | Not applicable | `Writing a brief for 006-x (gate 2, Risk: high)...` | `Refused: 004-x is Risk: low; briefs are for decisions people make` | `Wrote docs/changes/006-x/brief.md` |

## Copy
| key | Text | Notes |
|---|---|---|
| off | Refused: pod.yml sets loop: off. The sponsor turns the loop on with loop: on | loop.sh |
| not_autonomous | Refused: the loop runs only in mode: autonomous | loop.sh |
| dirty | Refused: the working tree has uncommitted changes; commit or stash them first | loop.sh |
| locked | Refused: another loop run holds .pod/loop.lock (started {age} ago) | loop.sh |
| kill | Refused: kill switch is on (.pod/kill-switch) | loop.sh, and before each step |
| people_gate | stopped: people sign gate {n} (Risk: {risk}) | per change |
| no_branch | stopped: branch change/{name} not found | per change |
| ready_to_merge | stopped: ready to merge: push the branch and open the PR (gh not available) | per change |
| step_failed | stopped: {step} failed ({reason}); nothing was committed | per change |
| limit | stopped: {stop reason from 0.9.0} | per change |
| summary | Loop run: {steps} steps, {stops} stops ({reasons}) | end of run |
| digest | loop runs: {steps} steps, {stops} stops ({by reason}) | digest section |

## Accessibility notes
- Plain text; one line per change and step, so CI logs stay readable.
- Every stop says who must act next: people, the sponsor, or nobody.
- Times in UTC; amounts in `US$` with two decimals.
