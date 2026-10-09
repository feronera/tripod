# Intent: Agent activity log and cost per change

Status: draft

## Problem
A pod cannot see what its agents did in a change or what the change cost. Today the only record is gates.log, which holds human signatures, and git history, which holds the result but not the agent work behind it (which skill ran, which files it touched, which commands it ran, how many tokens it used).

Evidence:
- In the tripod-example runs on 2026-10-08 and 2026-10-09, cost and agent time had to be reconstructed by hand after the fact: about US$8 / 30 min (Run A), about US$6.5 / 23 min (change 001, PR #1). Nothing in the repository records these numbers.
- When the session scratchpad was wiped on 2026-10-08, the Run A artifacts were lost, and there was no record left of what the agents had done.
- The README states that seeing what the agent does, and where, is essential for working on the loop (HOTL). Autonomous mode (roadmap steps 2 to 4) needs this record first: agent signatures, a budget per change and automatic stops on cost spikes all read from it.

## Users
- SuperBiz and SuperDev in a pod: see what the agents did in a change before signing a gate.
- The sponsor in Autonomous mode (planned): see cost per change and per day without reading transcripts.
- Teams adopting Tripod: compare agent cost between changes and over time (`scripts/metrics.sh`).

## Success measure
Share of changes in this repository with an agent activity record and a cost total kept in the change folder:
- Current value: 0 of 0 Tripod changes. In tripod-example, 0 of 3 changes had a recorded cost (all reconstructed by hand).
- Target: every change in this repository merged after this change has both (100%), starting with change 002.
- The cost total must be within <tolerance, see Open questions> of the cost Claude Code reports for the same sessions.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Tripod is public, and every adopting team gets the log through the plugins and scripts.
3. Rollback within minutes without data loss: yes. Removing the hook stops the logging; the log files are plain files in the change folder.
4. Personal or sensitive data: possibly. Commands, file paths and prompts can contain secrets or personal data, so what is logged must be limited and documented.

Question 4 is not a clear "no", and the work touches `scripts/**` and `plugins/**/hooks/**` (both in docs/risk-paths), so the change is high at merge time anyway.

## Constraints
- Python 3 stdlib only, as the rest of the kit.
- Works offline. No external service or telemetry endpoint is required.
- A project without pod.yml must keep working as today (hooks allow every action).
- Logging must never block or slow an agent action noticeably. A logging failure is reported, not fatal.
- Bootstrap pod: one maintainer with two accounts (feronera: SuperBiz and escalation, hx-natthawat: SuperDev).

## Open questions
- Where does the cost come from? The options are the Claude Code session transcripts, its usage or OpenTelemetry output, or the `claude -p` JSON result. SuperDev to check feasibility.
- What tolerance is acceptable between the logged cost and the cost Claude Code reports (for example ±5%)?
- What must never be logged? Proposal: no prompt text and no command output, only the tool name, the file paths, the command's first word, and timestamps.
- Should the log be committed to git with the change, or kept local with only the totals committed?
- Does this change include cost in `scripts/metrics.sh`, or is that left to a later change?
