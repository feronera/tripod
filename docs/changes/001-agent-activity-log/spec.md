# Spec: Agent activity log and cost per change

References: intent.md, ux-brief.md

## Requirements

Which change is active
- R1: The system must attribute agent activity to the change whose folder matches the current git branch: branch `change/NNN-<slug>` maps to `docs/changes/NNN-<slug>/`. On any other branch, or when that folder does not exist, nothing is recorded. (verified by: test)

Activity
- R2: The system must append one line to `docs/changes/NNN-<slug>/activity.log` after every agent tool call (PostToolUse) in a project with `pod.yml`. Each line has the fields `at`, `session`, `tool`, and, when they apply, `files` (paths relative to the repository root) and `cmd` (the first word of a Bash command only). (verified by: test)
- R3: The system must never write prompt text, file contents, tool output or the rest of a Bash command to activity.log. (verified by: test that feeds a command containing a token-like string and a tool output, and asserts that neither appears)
- R4: The system must record each tool call once, even when both the superbiz and superdev plugins are installed and both hooks run. Lines are de-duplicated by the tool call id. (verified by: test)
- R5: Paths outside the repository must be recorded as `<outside>`, not as the real path. (verified by: test)

Cost and agent time
- R6: At the end of every agent turn (Stop and SubagentStop), the system must append one `event=usage` line with the model and the tokens used since the last usage line of that session: `input`, `output`, `cache_write`, `cache_read`. The token counts come from the Claude Code session transcript (`transcript_path` in the hook input). Subagent turns are included. (verified by: test with a recorded transcript fixture)
- R7: Each usage line must also carry `usd`, computed from the tokens with the price table `docs/model-prices`, and `seconds`, the agent time of that turn (first to last message timestamp of the turn). (verified by: test)
- R8: Reading the transcript must be incremental: a per-session cursor in `.pod/activity/` (not committed) records how far the transcript has been read, so a long session is not re-read on every turn and no tokens are counted twice. (verified by: test that runs the hook twice on a growing transcript)
- R9: A model missing from `docs/model-prices` must still get its tokens logged, with `usd=unknown`, and a one-line warning on stderr naming the model and the price file. (verified by: test)
- R10: The cost total of a change must be within ±5% of `total_cost_usd` reported by `claude -p --output-format json` for the same sessions. (verified by: demo, a recorded `claude -p` run on a sample change in tripod-example, with both numbers in acceptance.md)

Viewing
- R11: `scripts/activity.sh <change-dir>` must print a summary: sessions, tool calls by tool, files touched (top 10 by count), tokens by model, cost, agent time, and the first and last activity time. (verified by: test)
- R12: `scripts/metrics.sh <change-dir>` must add two lines after the lead time: `agent time` and `agent cost`, taken from activity.log, or `no activity.log` when there is none. (verified by: test; existing metrics tests keep passing)

Safety and setup
- R13: A logging failure (unreadable transcript, unwritable folder, malformed price file) must never block the tool call or the turn: the hook exits 0 and prints one warning on stderr. (verified by: test)
- R14: In a project without `pod.yml`, the hooks must do nothing, as the existing hooks do. (verified by: test)
- R15: `activity.log` must be committed even when a global gitignore ignores `*.log`. `.gitignore` in this repository, and the lines `pod-install.sh` adds, must include `!docs/changes/*/activity.log`. `gate.sh` already refuses to sign when gates.log is ignored; the same check must warn when activity.log is ignored. (verified by: test)
- R16: The hook must add no more than 100 ms to a tool call on a typical change (median of 20 calls, measured in the test suite on this machine). (verified by: test)

Docs
- R17: A new page `docs/activity-log.md` must describe the fields, what is never logged, the price table and how to update it, and how to read the summary. README (command reference and roadmap step 1) and AGENTS.md must link to it. (verified by: demo, review of the docs)

## Edge cases
- E1: No activity.log yet (a change where no agent has worked): `activity.sh` prints the empty state from ux-brief.md and exits 0; `metrics.sh` prints `no activity.log`.
- E2: Malformed line in activity.log (edited by hand or a merge conflict): the line is skipped, the summary counts it as `skipped lines: N` and exits 0.
- E3: Branch switch in the middle of a session: each turn's usage goes to the change of the branch active at the end of that turn. Tokens from before the switch are not moved.
- E4: Two people work on the same change on different machines: both append to activity.log; git merges of append-only lines may conflict. Resolution: keep both sides (documented in docs/activity-log.md). `session` keeps their records apart.
- E5: Transcript missing, truncated or rotated: the cursor is reset, the turn is logged with `tokens=unknown`, and a warning is printed. No crash.
- E6: Price table file missing: every usage line gets `usd=unknown` (R9), and `activity.sh` prints the cost as `unknown (docs/model-prices not found)`.
- E7: Permissions and privacy: file paths outside the repository (for example `~/.ssh`) are recorded as `<outside>` (R5); command arguments are never recorded (R3).
- E8: Agent works on `main` or a non-change branch: nothing is logged (R1). The sponsor sees this as missing activity, not as an error.
- E9: A change merged with squash: activity.log is part of the change folder and survives the squash, like gates.log.

## Flagged concerns
- C1 (SuperDev, feasibility, checked 2026-10-09 on Claude Code 2.1.291): subagent work is written to separate transcript files, `<session transcript without .jsonl>/subagents/agent-*.jsonl`, next to the main transcript. R6 therefore reads the main transcript and every file in that `subagents/` folder, each with its own cursor (R8), at Stop and SubagentStop. If a future Claude Code version moves these files, R10 (the ±5% check) will show the gap.
- C2 (SuperBiz, accepted risk): the price table goes out of date when prices change. Proposal: `docs/model-prices` has one line per model with input, output, cache write and cache read prices per million tokens and an `as of` date, maintained by hand from the Anthropic pricing page. `activity.sh` prints the `as of` date next to the cost. A price table older than 90 days gets a warning. Updating it automatically is out of scope.
- C3 (SuperDev): hooks run from the installed plugin, but the logic lives in the project's `scripts/`. The plugin hook calls `scripts/lib.py` in the project when present, so the project's kit version decides the format. Projects on an older kit without the command keep working (the hook does nothing).
- C4 (escalation): activity.log is public in public repositories. R3 and R5 limit what is written, but file paths and command names are still visible. Teams with sensitive repository layouts can turn the activity log off with `activity_log: off` in pod.yml (default `on`).
- C5: this change touches `scripts/**` and `plugins/**/hooks/**`, so it is Risk: high at merge (matches intent.md).

## Out of scope
- Budgets, cost limits, automatic stops and the daily digest (roadmap step 3).
- Agent identities and agent signatures in gates.log (roadmap step 2).
- Activity from tools other than Claude Code.
- Updating the price table automatically or fetching prices online.
- A web dashboard. Output is text in the terminal and in CI logs.
- Recording activity after a change is merged (post-merge acceptance work is logged only if it happens on the change branch).
