---
name: brief
description: Write a one-page brief for people who must decide on a medium or high risk change waiting at a gate - the decision, options, risks, evidence and a recommendation. Read-only; signs nothing. Use from scripts/superceo.sh brief, or when asked "brief", "สรุปให้ตัดสินใจ", "escalation brief".
---

# Brief a decision (SuperCEO)

Goal: the escalation person, SuperBiz or SuperDev can decide in five minutes, with the evidence one click away.

## Steps
1. Read the change's artifacts up to the gate that is waiting, gates.log, activity.log, review.md and refusals.md if present.
2. Write Markdown with exactly these sections:
   - `## Decision`: the one question to answer, and which gate it signs.
   - `## Options`: two or three, each with what happens next.
   - `## Risks`: what could go wrong for each option, citing the 4 risk questions in docs/risk-tiers.md.
   - `## Evidence`: links to the files and lines that matter.
   - `## Recommendation`: one option and why, or "people should not sign yet" and what is missing.
3. Separate facts (with a file reference) from opinions.

## Do not
- Edit any file. The script writes your answer.
- Sign, approve or recommend skipping a gate.
