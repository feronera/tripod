---
name: plan
description: Write plan.md for an approved spec, data shape first, then a throughput checkpoint, parallel parts, files to change, order of work, risks, proof, rollback and a 3-line plain-language summary for SuperBiz. Always starts in plan mode. Use when the user says "วางแผน", "เขียน plan", "ทำ plan.md", "plan this change", "how do we build this".
---

# Write plan.md (SuperDev: SA)

Goal: a `docs/changes/NNN-slug/plan.md` that is ready for a human to sign gate 3.

## Steps
1. Always start in plan mode. If you are not in plan mode yet, ask the human to press Shift+Tab until plan mode is on.
   While in plan mode, read only. Do not edit files.
2. Check that gate 2 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 2`.
   If it fails, tell the human and stop.
3. Read intent.md, spec.md, ux-brief.md (if present), `docs/templates/plan.md` and `AGENTS.md`.
4. Read the related code in `app/` and tests in `tests/`.
5. Write `## Data shape` before anything else: the main data the code will use and the structure that organizes it,
   for example a table (dict), a state machine or a typed record. Choose a shape that makes invalid cases impossible
   and avoids `if` conditions scattered across files. When the data shape is right, the logic that follows is straightforward.
6. Write `## Throughput checkpoint` with all 4 lines (`n/a: <reason>` is allowed):
   - Blocking first steps: work that must finish before other work can start, such as failing tests or the data shape.
   - Independent workstreams: work that can proceed separately without waiting.
   - Shared mutable state: files or data that several parts must edit together.
   - Smallest safe decomposition: the smallest split where each piece ends in a check.
7. Write `## Parallel parts`:
   - If the work is not split, write `none: <reason>`.
   - If it is split, there must be at least 2 parts as `### <name>`, each with a `files: a.py, b.py` line,
     and no file may appear in more than one part. If parts must edit the same file, separate the state first, or do them one at a time.
8. Draft the remaining sections from the template:
   - Files to change: every file is tied to a requirement (R1, R2, ...).
   - Order of work: always start with failing tests, then lock the tests, then small units,
     each ending with `make test` passing.
   - Risks: technical risks and how to reduce them.
   - Proof: how each requirement is proven (which test or which demo).
   - Rollback: rollback steps that actually work.
9. The stack is the Python 3 standard library only. Never plan to add a dependency.
10. Add a `## Summary for SuperBiz` section of 3 lines, in the team's language (English by default), without technical terms:
    1. What will be done
    2. What users will see change
    3. Risks SuperBiz should know about
11. Present the plan for the human to approve. Write plan.md only after leaving plan mode.
12. Check the format with `scripts/gate-check.sh docs/changes/NNN-slug 3`.
    A `gate 3: plan.md ...` message names a missing section. Fix it until that message is gone.
    (A "no approval yet" message is normal before the humans sign.)
    `scripts/gate.sh` refuses a plan that is missing these sections.

## Do not
- Edit code or tests in this skill.
- Run `scripts/gate.sh` or edit `gates.log`.

## When done
Tell the human:
1. SuperDev runs `scripts/gate.sh docs/changes/NNN-slug 3`.
2. SuperBiz reads "Summary for SuperBiz", checks it still matches the intent, then runs the same command.
3. The next step is `/superdev:test-first`, then `/superdev:build`.
   If Parallel parts has several parts, see `docs/parallel-agents.md`.
   If two design approaches are still undecided, use `/superdev:arena`.
