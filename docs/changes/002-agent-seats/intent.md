# Intent: Agent seats and agent signatures (Autonomous mode for low risk)

Status: draft

## Problem
Agents draft every artifact, but only people can sign a gate. So even a low-risk change waits for two people at each of the four gates, and Autonomous mode (README, "Two modes") cannot start.

Evidence:
- In tripod-example, change 002 (low risk, PR #5, 2026-10-09) was merged by the agent through auto-merge. Before that it still needed 6 human signatures at gates 1 to 3.
- Tripod's own change 001 (2026-10-09) took 8 human signatures at gates 1 to 4 (plus 2 escalation signatures recorded with them). Each one meant stopping the agent, handing over, and the person running `gate.sh`.
- The roadmap's next step is "Agent identities and agent signatures (`role=agent`, with the model), with cross-checks on a different model". Steps 3 and 4 (sponsor controls, loop driver) depend on it.
- Since 0.7.0, activity.log records which model ran in which session. That is the evidence an agent signature can point to.

## Users
- Teams that want low-risk work to flow without a person at every gate: the sponsor sets the limits and reads the evidence.
- SuperBiz and SuperDev in Pod mode: no change for them unless the pod turns Autonomous mode on.
- Reviewers and auditors: they need to see which agent and which model signed, and to check that the cross-check really ran on a different model.

## Success measure
- Human signatures needed for a low-risk change in Autonomous mode: from 8 today to 1 (a person sets the risk at gate 1). Measured on one low-risk demo change in tripod-example, run end to end by agents after gate 1, with the sponsor able to stop it (kill switch) and revert it.
- Cross-checks that catch a planted defect: a spec that misses a requirement from intent.md, and a plan that misses a spec requirement, must be refused by the cross-checking agent in 3 of 3 runs each.
- Medium and high risk: 0 gates signed by agents (they still need people), proven by tests.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Teams that adopt Tripod get a new way to approve work.
3. Rollback within minutes without data loss: yes. `mode: pod` in pod.yml turns it off, and agent signatures are plain lines in gates.log.
4. Personal or sensitive data: no.

This changes who may approve work, which is governance (the "may not do alone" list in docs/pod-charter.md), and it touches `scripts/**`. It is high.

## Constraints
- Autonomous mode is off by default (`mode: pod`). A pod turns it on in pod.yml.
- Agents may sign only Risk: low changes. Medium and high always go to people, even in Autonomous mode.
- The cross-checking agent must run on a different model from the owner agent, and the signature records the model.
- An agent signature must point to evidence in activity.log (the session and model that did the check), so a reviewer can trace it.
- People can still sign every gate. A person's signature always counts.
- The sponsor keeps the existing controls: kill switch, revert (`mark-revert.sh`), and branch protection.
- Tripod's own repository stays in Pod mode with bootstrap on (PO decision, 2026-10-09).
- Python 3 stdlib only.

## Decided (PO, 2026-10-09)
- Scope: Autonomous mode for Risk: low only. Medium and high stay with people.
- Budget per change and per day, risk ceiling, automatic stops and the daily digest are change 003. The loop driver and the superceo agent are change 004.
- Tripod's own pod keeps bootstrap mode and Pod mode after this change.
- Gate 1 always has a person: a person signs intent.md and so decides that the change is low. Agents may sign gates 2 to 4 of a low-risk change. Risk can still only go up after gate 1, and docs/risk-paths still makes a change high at merge.
- The sponsor is named in pod.yml (`sponsor_name`, `sponsor_email`, `sponsor_github`) and signs nothing else. The sponsor is on the loop: reads the evidence in the PR, gates.log and activity.log after merge, and can use the kill switch and revert.

## Open questions
- Feasibility (SuperDev, for the spec): an agent signs through a separate command, not `gate.sh`, which stays for people. The command writes `role=owner` or `role=cross` with `by=agent:<leg>`, `model=<model>` and `session=<id>`. gate-check accepts it only in Autonomous mode, only at Risk: low, only at gates 2 to 4, and only when activity.log has usage for that session and model. How the cross-checking agent is started on a different model (for example `claude -p --model`) is decided in the plan.
