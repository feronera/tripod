---
name: spec
description: Turn intent.md and ux-brief.md into spec.md with numbered requirements, edge cases, flagged concerns and out-of-scope, using the ba-researcher agent for code impact. Use when the user says "เขียน spec", "ทำ spec", "แปลง intent เป็น spec", "write the spec", "spec this change".
---

# Draft spec.md (SuperBiz: BA)

Goal: a `docs/changes/NNN-slug/spec.md` that is ready for a human to sign gate 2.

## Steps
1. Read intent.md, ux-brief.md (if present) and `docs/templates/spec.md`.
2. Check that gate 1 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 1`.
   If it fails, tell the human and stop.
3. Send a question to the `ba-researcher` agent, for example:
   "Which code or data does this intent touch, and which existing behavior must be kept?"
   Use only answers that cite files.
4. Write Requirements as R1, R2, ... Start each one with "The system must" and state how it is verified (test or demo).
5. Write Edge cases as E1, E2, ... Cover:
   - Empty or not-found data
   - Malformed data
   - Permissions: users must never see other users' data
   - The states from ux-brief.md
6. Flagged concerns: conflicts with existing code, risks found, and questions a human must decide, with file references.
7. Out of scope: what this change will not do, to prevent scope creep.
8. If the ba-researcher findings suggest the Risk in intent.md is too low, say so under Flagged concerns.
   Never edit intent.md yourself, because gate 1 would become stale.
9. Check against the Gate 2 questions in `docs/gates.md`.

## Do not
- Run `scripts/gate.sh` or edit `gates.log`.
- Edit files outside `docs/`.

## When done
Tell the human:
1. SuperBiz runs `scripts/gate.sh docs/changes/NNN-slug 2`.
2. SuperDev cross-checks it, then runs the same command.
3. If `Risk: high`, the person named as escalation in pod.yml must also run the same command.
