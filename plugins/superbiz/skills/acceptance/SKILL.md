---
name: acceptance
description: Business-side gate 4 check. Compare the PR against the Success measure in intent.md, run or collect demo steps, and write acceptance.md with accept or reject plus reason. Use when the user says "ตรวจรับงาน", "acceptance", "รับมอบงาน", "UAT", "accept the PR".
---

# Write acceptance.md (SuperBiz: gate 4 acceptance)

Goal: a `docs/changes/NNN-slug/acceptance.md` that states accept or reject, with the reason.

## Steps
1. Read intent.md (Success measure), spec.md (Requirements) and `docs/templates/acceptance.md`.
2. Check that gate 3 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 3`.
   Check `gates.log` for a `role=auto` line (already auto-merged, awaiting acceptance).
3. Ask the human for a summary of the PR's changes, or read it with `git diff main...HEAD --stat`.
   Summarize it in language a non-developer can understand.
4. Use the demo steps SuperDev provided in plan.md or the PR. If there are none, ask the human. Never make up steps.
5. Run the demo one step at a time. Record the expected result and the actual result.
6. Compare the results against the Success measure, item by item.
   - If it can only be measured after release, state how it will be measured and on what date.
7. Write the Decision: `accept` or `reject`, with a reason that cites the demo results.
   If rejecting, list what must be fixed as bullet points.
8. Never decide on the human's behalf. Propose a decision and let SuperBiz confirm it.

## Do not
- Run `scripts/gate.sh` or edit `gates.log`.
- Edit code or tests.

## When done
Tell the human:
1. SuperDev (owner of gate 4) runs `scripts/gate.sh docs/changes/NNN-slug 4` first.
2. SuperBiz confirms the decision, then runs the same command.
3. If `Risk: high`, the escalation person must also run the same command.
4. For a low-risk change that was already auto-merged (a `role=auto` line in gates.log), this is acceptance after merge.
   SuperBiz may sign before SuperDev, and must do so within `acceptance_hours` in pod.yml.
   SuperDev then signs as owner against the same acceptance.md.
5. If rejecting after merge, SuperBiz or SuperDev considers `git revert` and
   `scripts/mark-revert.sh docs/changes/NNN-slug "<reason>"` (a human runs these).
