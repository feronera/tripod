# Intent: Loop driver and the SuperCEO agent

Status: draft

## Problem
Autonomous mode (0.8.0, 0.9.0) has agent seats, limits and a digest, but nothing moves the work. A person still has to start an agent for every step: draft the spec, run agent-sign, build, review, run auto-merge-check. On the 0.8.0 demo change, getting from gate 1 to merge took 14 commands typed by hand. Nothing decides which change to work on next, and nothing prepares the decisions people must make on high-risk work.

Evidence:
- The demo for change 004 in tripod-example needed 14 commands by hand between gate 1 and the auto-merge. Each was obvious from the change's state: which artifact is missing, which gate is next.
- The README roadmap step 4, and the "Two modes" table, promise a loop that runs on a schedule and a `superceo` agent for priorities and high-risk briefs. Neither exists, so Autonomous mode is not autonomous yet.
- Sponsors read the digest, but nobody ranks what should happen next or summarises a high-risk change for the escalation person.

## Users
- The sponsor: turns the loop on, reads the digest and SuperCEO's ranking, decides high-risk briefs.
- Pod members: still sign gate 1 and every medium or high gate. The loop prepares that work and waits for them.
- Teams on Pod mode: unaffected. The loop does nothing unless the pod is in `mode: autonomous`.

## Success measure
In a demo in a copy of tripod-example:
- Commands typed by a person between gate 1 and merge for a low-risk change: from 14 to 0. People only sign gate 1. The loop runs on a schedule or by hand, and every limit from 0.9.0 still stops it.
- Every loop run leaves a record of what it did and why it stopped, in activity.log and in the digest. Target: 100% of runs.
- For a high-risk change, SuperCEO writes a brief before the escalation signature is needed. The brief must state the decision, the options, the risks and the evidence links. Target: 1 brief in the demo, accepted as useful by the PO.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Teams that adopt Tripod get agents that act without a person starting each step.
3. Rollback within minutes without data loss: yes. Turn the loop off (`loop: off`, or the kill switch); everything it did is in git and the logs.
4. Personal or sensitive data: no.

It runs agents with no person starting them and touches `scripts/**`, so it is high.

## Constraints
- Python 3 stdlib only. The loop calls `claude -p` like agent-sign does.
- Off by default (`loop: off`). It runs only in `mode: autonomous`.
- The loop never signs a gate as a person, never runs `gate.sh`, `resume.sh` or `mark-revert.sh`, and never merges medium or high risk.
- Every 0.9.0 limit applies: budgets, refusals, the revert pause, the ceiling and the kill switch.
- Medium and high risk: one step per run at most. The loop drafts the next artifact, and SuperCEO writes the brief, then they wait for people.

## Decided (PO, 2026-10-10)
- Where it runs: one command, `scripts/loop.sh`, which does one loop run. It works from cron on a machine and from a scheduled GitHub Actions workflow. The kit ships an example workflow that is turned off.
- Pace: one step per run, or until blocked, chosen by the sponsor in pod.yml for low-risk changes. Medium and high risk always take one step per run and then wait for people.
- SuperCEO ranks the open changes and the backlog, and writes briefs for high-risk decisions for people. It signs nothing, including escalation.

## Open questions
- None.
