# Acceptance: Loop driver and the SuperCEO agent

References: intent.md, spec.md (scope amended 2026-10-11). Evidence: [demo/final](demo/final/); the first, larger version: [demo/first-version](demo/first-version/)

## Success measure check
| Success measure (amended) | How measured | Result | Pass? |
|---|---|---|---|
| Steps started by a person between gate 1 and the end of gate 3, for a low-risk change: from 6 to 0 | Change 007 in a copy of tripod-example, final code ([loop runs](demo/final/loop-runs.txt), [gates log](demo/final/007-order-note-count/gates-log.txt)) | 0. Six loop runs: spec, gate 2 owner and cross, plan, gate 3 owner and cross, all signed by agents on two models and approved first time. The seventh run stopped with "people build". About US$0.75 and 2 minutes ([summary](demo/final/007-summary.txt)) | Yes |
| Every loop run leaves a record | activity.log of 007 and 008 (event=loop), [digest](demo/final/digest.txt) | Every step and stop is recorded. The digest on main shows changes on main only; branch records appear once merged | Yes, in activity.log |
| SuperCEO writes a brief before a high-risk decision | Change 008 ([brief](demo/final/008-delete-account/brief.md)) | Written as soon as 008 stopped at gate 2. It points out that the agent wrote two legal decisions as "Decided", and gives options A, B and C | Pending your judgement: was it useful? |
| A priorities file | [priorities](demo/final/priorities.md) | All 8 changes ranked, with state, next step, blocker and spend. It calls 008's intent a placeholder, which it is | Yes |

## Demo steps
1. A person signs gate 1 of 007 (low) and 008 (high); `scripts/loop.sh --change …` runs repeatedly.
   - Expected result: 007 reaches "people build"; 008 stops at gate 2 with a brief.
   - Actual result: as expected.
2. `scripts/superceo.sh priorities`, `scripts/loop.sh --dry-run`, `scripts/digest.sh`.
   - Expected result: files and output as above.
   - Actual result: as expected. The dry run also skipped 006, whose branch cannot be checked out cleanly, and named it.

What the first version taught (demo/first-version):
- The automatic build, merge and acceptance worked in part (12 of 13 steps on change 006).
- They needed many more safeguards. That led to the scope cut.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason:
- On the final code the loop took a low-risk change from gate 1 to "people build" with no person starting a step.
- It stopped a high-risk change for people with a useful brief.
- Three review rounds closed every Blocker.

Open item for the PO: judge the 008 brief.
