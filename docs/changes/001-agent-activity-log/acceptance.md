# Acceptance: Agent activity log and cost per change

References: intent.md (Success measure), PR: to be opened after gate 4

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| Cost total within ±5% of Claude Code's own number | R10 demo below, final code (commit in review.md) | US$0.4639 logged vs US$0.4700 `total_cost_usd`: -1.29% | Yes |
| Cost method matches Claude Code across real sessions | Transcripts of one maintainer's past sessions, compared with Claude Code's `cost-state` records | Opus 5.5: within 1% in 101 of 103 sessions; Opus 4.7: 362 of 364 | Yes |
| `scripts/metrics.sh` shows agent cost and agent time | Tests test_metrics_lines and test_activity_time_line_and_metrics_order | Both lines printed after the lead time | Yes |
| Every change merged after this one has an activity record and a cost total (100%, starting with change 002) | `scripts/activity.sh` on change 002 and later | Measured after release, at the gate 4 of change 002 | After release |

## Demo steps
1. In a copy of tripod-example with the 0.7.0 scripts, create branch `change/090-r10-demo` and its folder.
   - Expected result: the hooks record to `docs/changes/090-r10-demo/activity.log`.
   - Actual result: as expected.
2. Run `claude -p "<read two files, one through a subagent, write a summary>" --plugin-dir tripod/plugins/superdev --output-format json`.
   - Expected result: tool records for Read, Agent and Write; usage records for the main session and the subagent; no prompt text, file contents or command arguments in the log.
   - Actual result: 5 tool records (Agent, Bash, Read, SubagentHandback, Write); usage records for main and the subagent; no prompt text or content.
3. Run `scripts/activity.sh docs/changes/090-r10-demo` and compare with `total_cost_usd`.
   - Expected result: within ±5%.
   - Actual result: `cost: US$0.46 (prices as of 2026-10-09)`; exact US$0.4639 vs US$0.4700, -1.29%. The gap is a Haiku background call (US$0.001) that is not in the transcript, and output tokens the transcript records slightly lower than billed.
4. Run `scripts/activity.sh` on a change with no activity.
   - Expected result: the empty-state copy from ux-brief.md.
   - Actual result: as expected (test_empty).

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: the cost check passes (-1.29% against the ±5% limit), the method reproduces Claude Code's own cost in 99% of past sessions, and the privacy rules decided at gate 1 hold under review (no prompts, content or arguments; secrets and outside paths are kept out). The success measure for later changes can only be measured from change 002 onwards. Open item for the PO: accept the three spec-text deviations listed in review.md (SessionEnd, one record per transcript and model, `cache_write_1h`).
