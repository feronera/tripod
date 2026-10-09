# Agent activity log and cost per change

Every change keeps a record of what the agents did and what it cost, in `docs/changes/NNN-slug/activity.log` next to `gates.log`. People read it before signing a gate. In Autonomous mode (planned), the sponsor's budget and automatic stops will read from it.

## How it is recorded

The `superbiz` and `superdev` plugins run `scripts/activity.py` from three Claude Code hooks:

| Hook | Writes |
|---|---|
| PostToolUse (every tool) | one `event=tool` record |
| Stop (end of a turn), SubagentStop and SessionEnd | one `event=usage` record per transcript and model with new tokens. Claude Code writes a session's last response after the Stop hook, so SessionEnd picks it up |

Activity goes to the change whose folder matches the current branch: branch `change/001-agent-activity-log` writes to `docs/changes/001-agent-activity-log/activity.log`. On any other branch, or in a project without `pod.yml`, nothing is recorded.

Logging never blocks the agent. If something fails (no transcript, a folder that cannot be written), the hook prints one line, `activity log not written: … The tool call was not affected`, and the work goes on.

## Fields

```
event=tool at=2026-10-09T14:02:11Z session=7db0… id=toolu_01… tool=Edit files=scripts/lib.py
event=tool at=2026-10-09T14:02:15Z session=7db0… id=toolu_02… tool=Bash cmd=make
event=usage at=2026-10-09T14:03:40Z session=7db0… agent=main model=claude-opus-5-5 input=12 output=1840 cache_write=21368 cache_write_1h=21368 cache_read=48210 usd=0.199204 seconds=92
```

| Field | Meaning |
|---|---|
| `session` | Claude Code session id; tells people and machines apart |
| `id` | Tool call id; a call is recorded once even when both plugins are installed |
| `files` | Paths relative to the repository, comma-separated. A path outside the repository is written as `<outside>` |
| `cmd` | The program a Bash command ran (`make`, `git`, `gh`), without its arguments or `VAR=value` prefixes |
| `agent` | `main`, or the subagent id |
| `input`, `output`, `cache_write`, `cache_read` | Tokens since the last usage record. `cache_write_1h` is the part of `cache_write` cached for one hour |
| `usd` | Cost of those tokens, from `docs/model-prices`, or `unknown` |
| `seconds` | Time of the turn, first to last message. Subagent time is recorded but not added to agent time, because subagents run inside the main turn |

## What is never logged

- Prompt text or any message content
- File contents
- Tool output
- Command arguments, including tokens, passwords and `VAR=value` prefixes
- Paths outside the repository

In a public repository, file paths and command names are still visible to everyone. To turn the log off, set `activity_log: off` in `pod.yml`.

## Cost

Claude Code transcripts record tokens per message and model, but no cost. `scripts/activity.py` counts each API response once (Claude Code writes one response on several lines with the same message id), includes subagent transcripts (`<session>/subagents/agent-*.jsonl`), and prices the tokens with `docs/model-prices`. One-hour cache writes are priced separately from five-minute ones.

Checked on 2026-10-09 with this code against the cost Claude Code itself records (`cost-state` in the transcripts) for one maintainer's sessions: Opus 5.5 within 1% in 101 of 103 sessions and within 5% in 102; Opus 4.7 within 1% in 362 of 364 and within 5% in 363. Sessions whose transcript was incomplete were left out of the check.

Two small gaps remain. Claude Code's own background calls (for example a small Haiku classifier, about US$0.001 per session) are not in the transcript, so they are not counted. And the transcript can record slightly fewer output tokens than Claude Code bills. In the change 001 demo (`claude -p`, with a subagent) the logged cost was 1.4% below `total_cost_usd`.

### Updating the price table

`docs/model-prices` has one line per model, prices in US$ per million tokens, and an `as_of` date:

```
as_of: 2026-10-09
claude-opus-5-5              4      20      5               8               0.2
```

When prices change or a new model is used, update the line and the date from the Anthropic pricing page. A model missing from the table is still recorded with `usd=unknown`, and the hook prints a warning naming it. `scripts/activity.sh` warns when the table is more than 90 days old.

## Reading it

```
$ scripts/activity.sh docs/changes/001-agent-activity-log
change: 001-agent-activity-log   Risk: high
activity: 2026-10-09 14:02 → 2026-10-09 16:40   sessions: 3
tool calls: 214   Bash 92, Read 61, Edit 38, Write 15, Grep 8
files (top 10): scripts/lib.py 41, tests/test_activity.py 22, ...
tokens: claude-opus-5-5  in 1.2M  out 84k  cache write 310k  cache read 9.8M
cost: US$6.48 (prices as of 2026-10-09)
agent time: 0h 23m
```

`scripts/metrics.sh <change-dir>` adds `agent time` and `agent cost` under the lead time.

## Committing it

`activity.log` is committed with the change, like `gates.log`. The hooks append to it while the agent works, so commit it with each commit. A global `*.log` gitignore rule would hide it: `.gitignore` needs `!docs/changes/*/activity.log` (`pod-install.sh` adds it, and `gate.sh` warns when it is missing).

If two people work on the same change, a git merge can conflict on activity.log. Keep both sides: every line is a separate record, and `session` keeps them apart. Lines that are not records (such as conflict markers) are skipped and counted in the summary.
