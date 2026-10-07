# Risk tiers

Declare the risk tier in `intent.md` on a single line, e.g. `Risk: medium`.
The tier follows from the answers to 4 questions.

| # | Question | A "yes" means |
|---|---|---|
| 1 | Does it involve law or regulation (e.g. data protection, finance, contracts)? | Higher risk |
| 2 | Do customers or external users see the result directly? | Higher risk |
| 3 | Can it be rolled back within minutes without data loss? | Lower risk |
| 4 | Does it touch personal or sensitive data? | Higher risk |

## Tiers

| Tier | Criteria | What changes |
|---|---|---|
| low | Questions 1, 2 and 4 are "no", and question 3 is "yes" | The normal 4 gates (owner + cross) |
| medium | Question 2 is "yes", questions 1 and 4 are "no", and it can be rolled back | Normal gates; plan.md needs a rehearsed Rollback; acceptance needs a demo with realistic sample data |
| high | Question 1 or 4 is "yes", or question 3 is "no" | As medium, plus an additional escalation signature at gate 2 and gate 4 (the person named in `pod.yml`) |

## Notes
- If unsure, choose the higher tier and give the reason in Open questions.
- The risk tier can change, but editing intent.md after gate 1 makes the gate 1 approval stale, and it must be signed again.
- Work on the "What the pod may not do alone" list in `docs/pod-charter.md` is always high.
- A change that touches a path in `docs/risk-paths` is always high at merge time (auto-merge-check and pr-check check the actual diff),
  even if intent.md declares a lower tier. Merge rights by tier are in `docs/merge-by-risk.md`.
