# Spec: Sponsor controls (budget, ceiling, automatic stops, daily digest)

References: intent.md, ux-brief.md

## Requirements

Limits in pod.yml (all optional; a missing key means no limit, today's behavior)
- R1: The system must read these keys:
  - `budget_per_change_usd` and `budget_per_day_usd` (decimal);
  - `max_refusals_per_gate` (integer);
  - `agent_merges_per_day` (integer);
  - `agent_forbidden_paths` (comma-separated globs).

  `gate-check --all` must fail when a value is malformed (not a number, or negative). (verified by: test)
- R2: The limits must apply only to agent work: `scripts/agent-sign.sh` and the auto-merge path. People's commands (`gate.sh`, pr-check approvals) are never limited. (verified by: test)

Spend
- R3: The system must compute spend from activity.log usage records (0.7.0). Spend per change is the sum of `usd` in that change's activity.log. Spend per day is the sum of `usd` with `at` in the last 24 hours, across every change in docs/changes. Records with `usd=unknown` count as 0 and are reported as unknown. (verified by: test)

Automatic stops (checked by agent-sign before any agent starts)
- R4: Budget. agent-sign must refuse when spend plus the estimated next run would exceed `budget_per_change_usd` for the change, or `budget_per_day_usd` for the pod. The estimate is the most expensive agent-sign run recorded in the last 7 days (0 when there is none). The refusal names the limit, the spend and the estimate. (verified by: test)
- R5: Refusals in a row. agent-sign must refuse when the gate already has `max_refusals_per_gate` refused agent checks since the last time a person acted on that change. A person acts by signing any gate of the change, or by running `scripts/resume.sh <change-dir> "<reason>"`. (verified by: test)
- R6: Revert. agent-sign must refuse while any change has an `event=revert` in the last 24 hours. (verified by: test)
- R7: `scripts/resume.sh <change-dir> "<reason>"` must record `event=resume by=<git email> at=… reason="…"` in gates.log. It is refused unless the git email is the sponsor's or a pod member's. It resets R5 only; it does not lift a budget or the revert window. (verified by: test)

Risk ceiling
- R8: agent-sign must refuse, and auto-merge-check must DENY, when the branch touches a path matching `agent_forbidden_paths`. These paths stay low risk for people. (verified by: test)
- R9: auto-merge-check must DENY when `agent_merges_per_day` auto-merge records (`role=auto`) already exist with `at` in the last 24 hours. (verified by: test)

Warning in the agent's session
- R10: When the change's or the day's budget is reached, the activity hook (PostToolUse) must add one message to the agent's context, at most once per session per limit. The message says which limit was reached and that agent-sign will refuse until the sponsor raises it. The hook still never blocks the tool call. (verified by: test)

Daily digest
- R11: `scripts/digest.sh [--hours N]` must print, for the last N hours (default 24):
  - spend: total, per change and per model, and the unknown part;
  - agent signatures, as gate, role and model per change;
  - refused agent checks per change;
  - auto-merges;
  - reverts;
  - resumes;
  - stops in force, with the reason;
  - the limits from pod.yml.

  The numbers must match activity.log and gates.log exactly. (verified by: test)
- R12: `scripts/digest.sh --write` must also save the output to `docs/digest/YYYY-MM-DD.md` (UTC date), overwriting that day's file. (verified by: test)

Demo and docs
- R13: A demo in a copy of tripod-example must show, with the real claude:
  - the budget stop (no run starts over budget);
  - the refusal stop after N refusals;
  - the forbidden-path stop;
  - a digest that matches the logs.

  (verified by: demo, recorded in acceptance.md)
- R14: docs/autonomous.md ("The sponsor"), README (roadmap step 3), AGENTS.md (agents must not run `resume.sh`) and the pod.yml template must describe the keys and commands. (verified by: review)

## Edge cases
- E1: Empty: no activity.log anywhere means spend 0. No gates.log means no refusals or reverts. The digest prints "nothing in the last 24 hours" for each empty section.
- E2: Malformed: `usd=unknown` or a bad number counts as 0 and is listed as unknown. A bad `at` is left out of the day's window and counted in the digest as skipped. A malformed limit in pod.yml fails `gate-check --all` (R1), and agent-sign refuses with the same message.
- E3: Permissions: `resume.sh` by an email that is not the sponsor or a member is refused. Agents must not run it (AGENTS.md); the record carries the git email, which the sponsor reads in the digest.
- E4: Budget exactly reached (spend + estimate = budget): allowed; only "would exceed" refuses.
- E5: No earlier agent-sign run: the estimate is 0, so only spend already over the limit refuses.
- E6: Time zones: all windows use UTC times from the logs (`at` with an offset is converted).
- E7: Pod mode: agent-sign already refuses. The digest still works and shows spend, which helps Pod-mode teams too.
- E8: Many changes: the daily spend reads every change's activity.log once per call.

## Flagged concerns
- C1 (SuperBiz): the estimate uses the most expensive recent run. A run can still cost more than that, so the day's spend can end slightly above the budget. The digest shows this. A hard cap would have to kill a running session, which the PO ruled out.
- C2 (SuperDev): `resume.sh` is a person's command like `gate.sh`. Like gate.sh, it trusts the git email. An agent that ignores AGENTS.md could run it; that falls under the accepted forgery risk of change 002, and the digest lists every resume with its email.
- C3: this change touches `scripts/**`, so it is Risk: high at merge.

## Out of scope
- Stops on repeated CI failures (PO, 2026-10-10).
- Sending the digest to Slack, email or an issue.
- Killing a running agent session.
- Budgets per person or per model.
