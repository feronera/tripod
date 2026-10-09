# UX brief: Agent activity log and cost per change

References: intent.md

The users are SuperBiz, SuperDev and (later) the sponsor, in a terminal or in a CI log. All output is plain text, readable without color, and stable enough to paste into a PR or acceptance.md.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/activity.sh <change-dir>` | See what the agents did in one change and what it cost, before signing a gate | sessions, tool calls by tool, top 10 files, tokens by model, cost, agent time, first and last activity, price table date | Read, then sign the gate or ask the agent why |
| `scripts/metrics.sh <change-dir>` (two new lines) | Compare changes: lead time next to agent time and cost | `agent time`, `agent cost` | Compare with earlier changes |
| Hook warnings (stderr in the agent session) | Tell the agent and the person that logging did not work, without stopping the work | one line: what failed and the file to check | Fix the price table or ignore rule later |
| `activity.log` (file) | The raw record, committed with the change | one `key=value` line per tool call or turn | Read in a PR diff |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| `activity.sh` | `No agent activity recorded for 001-agent-activity-log yet (no activity.log). Agents record activity on branch change/001-agent-activity-log in a project with pod.yml.` Exit 0 | Not applicable: reads one local file, no waiting state | Folder not found: `change folder not found: <path>`, exit 1. Malformed lines: summary as usual plus `skipped lines: N`, exit 0. Unknown price: `cost: US$4.12 + unknown (claude-x has no price in docs/model-prices)` | The summary below |
| `metrics.sh` | `agent time: no activity.log` and `agent cost: no activity.log` | Not applicable | Same as activity.sh for unknown prices | `agent time: 0h 23m` and `agent cost: US$6.48 (prices as of 2026-10-01)` |
| Hook | Silent when nothing to record (no pod.yml, not a change branch) | Not applicable | One stderr line per failure, never blocks (see Copy) | Silent |

Success example for `activity.sh`:
```
change: 001-agent-activity-log   Risk: high
activity: 2026-10-09 14:02 → 2026-10-09 16:40   sessions: 3
tool calls: 214   Bash 92, Read 61, Edit 38, Write 15, Grep 8
files (top 10): scripts/lib.py 41, tests/test_activity.py 22, ...
tokens: claude-opus-5-5  in 1.2M  out 84k  cache write 310k  cache read 9.8M
cost: US$6.48 (prices as of 2026-10-01)
agent time: 0h 23m
```

## Copy
| key | Text | Notes |
|---|---|---|
| empty | No agent activity recorded for {change} yet (no activity.log). Agents record activity on branch change/{change} in a project with pod.yml. | activity.sh, exit 0 |
| skipped | skipped lines: {n} (not in key=value form) | after the summary |
| unknown_price | {model} has no price in docs/model-prices, so its cost is unknown. Tokens are still recorded | hook stderr and summary |
| stale_prices | docs/model-prices is {days} days old (as of {date}). Check the Anthropic pricing page | summary, when older than 90 days |
| hook_failed | activity log not written: {reason}. The tool call was not affected | hook stderr |
| log_ignored | activity.log is ignored by git (often a global *.log rule), so it would never be shared. Add '!docs/changes/*/activity.log' to .gitignore | gate.sh warning, same tone as the gates.log message |
| off | Activity log is off in pod.yml (activity_log: off) | activity.sh when turned off |

## Accessibility notes
- Plain text only; no color or symbols carry meaning on their own.
- Numbers have units (US$, h/m, k/M tokens) so screen readers and CI logs read them correctly.
- Lines stay under 100 characters except file lists, which wrap per file in `--all` output (not in this change).
- The output is stable (same order every run) so it can be pasted into acceptance.md and compared.
