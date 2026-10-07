---
name: incident
description: Turn an application log into a draft change. Decide severity, never copy personal data, create a change with scripts/new-change.sh and fill intent.md citing log lines. Use when the user says "มี incident", "อ่าน log", "ระบบมีปัญหา", "incident", "triage this log".
---

# Turn an incident into a change (SuperDev: MA)

Goal: a draft intent.md that cites evidence from the log and contains no personal data.

## Steps
1. Ask the human for the log file path (for example `logs/sample-app.log`). Never guess the path.
2. Send the path to the `monitor` agent to read and summarize, or read it yourself with read-only tools.
3. Decide the severity:
   - SEV1: many users cannot use the system, or data has leaked.
   - SEV2: a core feature fails for some users.
   - SEV3: a minor failure with a workaround.
4. Never copy personal data such as names, phone numbers, emails, addresses or ID numbers.
   Cite line numbers instead, and replace the values with `[personal data removed]`.
5. If the evidence is not enough (fewer than 2 consistent lines, or the cause is only a guess),
   stop and ask the human. Do not create a change.
6. Ask the human to run `scripts/new-change.sh <slug>` (it refuses when the WIP limit is reached; relay that to the human).
7. Write intent.md from the template:
   - Problem: the symptom, number of occurrences and time window, citing `logs/...:<line>`.
   - Success measure: for example, errors per hour from X to 0. Use numbers from the log only.
   - Risk: per `docs/risk-tiers.md`. If the log contains personal data, consider `Risk: high`.
   - Open questions: what the log does not tell you.
8. For SEV1, notify the escalation person from pod.yml immediately, and recommend that the human consider the kill switch.

## Do not
- Run `scripts/gate.sh` or edit log files.

## When done
Tell the human that intent.md is a draft, and that SuperBiz reviews it and owns gate 1.
