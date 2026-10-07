---
name: intent
description: Draft intent.md for a new change with the PO, one question at a time, including Risk tier. Use when the user wants to start a change, write an intent, or says "ร่าง intent", "เริ่มงานใหม่", "เขียน intent.md", "draft intent", "new change".
---

# Draft intent.md (SuperBiz: PO)

Goal: a `docs/changes/NNN-slug/intent.md` that is ready for a human to sign gate 1.

## Steps
1. Ask which change to work on. If the folder does not exist yet, ask the human to run `scripts/new-change.sh <slug>`
   and wait for the path it prints. (The command refuses when the WIP limit is reached. Relay its message to the human.)
2. Read `docs/templates/intent.md`, `docs/risk-tiers.md` and the intent.md in the change folder.
3. Interview the PO one question at a time. Wait for each answer before asking the next. Use this order:
   1. What is the problem, who has it, and what is the evidence?
   2. Who are the users or the people affected?
   3. What number is the Success measure? What is the current value, the target, and by when?
   4. The 4 questions in `docs/risk-tiers.md`, one at a time.
   5. What constraints apply?
4. Set the Risk using the criteria in `docs/risk-tiers.md`. If unsure, choose the higher tier.
   Write exactly one line: `Risk: low`, `Risk: medium` or `Risk: high`.
5. Write intent.md from the template. Keep `Status: draft`.
6. Never invent numbers or facts. Put anything the PO does not know under Open questions.
7. Check against the Gate 1 questions in `docs/gates.md` and report any that do not pass yet.

## Do not
- Run `scripts/gate.sh` or edit `gates.log`.
- Edit files outside `docs/`.

## When done
Tell the human:
1. SuperBiz reviews intent.md, then runs `scripts/gate.sh docs/changes/NNN-slug 1`.
2. Ask SuperDev to cross-check it (feasible and measurable?), then run the same command.
3. Check the result with `scripts/gate-check.sh docs/changes/NNN-slug`.
