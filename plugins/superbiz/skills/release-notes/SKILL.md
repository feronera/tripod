---
name: release-notes
description: Write release notes for customers and for internal teams from a change folder, in the team's language (English by default). Use when the user says "เขียน release notes", "ประกาศการเปลี่ยนแปลง", "แจ้งลูกค้า", "release notes", "changelog for customers".
---

# Write release notes (SuperBiz: PM)

Goal: a `docs/changes/NNN-slug/release-notes.md` in two parts: one for customers and one for internal teams.
Write it in the team's language (English by default).

## Steps
1. Read the change's intent.md, spec.md, acceptance.md and runbook.md (if present).
2. Check that it is ready to release: `scripts/release-check.sh docs/changes/NNN-slug`.
   If it fails, write a draft and make the first line "Draft: not ready to release".
3. Customer section:
   - At most 5 lines, in polite, plain language.
   - Say what users get, and whether they need to do anything.
   - No technical terms, no file names, no internal information.
4. Internal section (customer support, sales, operations):
   - What changed, citing R1, R2, ... from spec.md.
   - What did not change (Out of scope).
   - Questions customers may ask, with answers.
   - Where to report problems, and a short summary of how to roll back, from runbook.md.
5. Never promise anything that is not in spec.md, and never state numbers that are not in acceptance.md.

## Do not
- Edit files outside `docs/`.

## When done
Ask the human to review the wording before publishing, and to send the internal section to the teams involved.
