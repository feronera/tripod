---
name: ux-brief
description: Act as the pod designer and write ux-brief.md (screens, empty/loading/error/success states, UI copy in the team's language, accessibility) from an approved intent. Use when the user says "ทำ ux brief", "ออกแบบหน้าจอ", "เขียนข้อความบนหน้าจอ", "ux brief", "design the screens".
---

# Draft ux-brief.md (SuperBiz: Designer)

Goal: a `docs/changes/NNN-slug/ux-brief.md` that accompanies spec.md at gate 2.

## Steps
1. Read the change's intent.md and `docs/templates/ux-brief.md`.
2. Check that gate 1 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 1`.
   If it fails, tell the human and stop.
3. List the screens needed and the purpose of each. Use the fewest screens that meet the intent.
4. Every screen must have all 4 states: empty, loading, error, success.
   - An error must tell the user what they can do next.
   - An error must never reveal other users' data, or that other users' data exists.
5. Write the copy users actually see, in the team's language (English by default). Keep it polite, short and clear.
6. Write accessibility notes: screen reader support, meaning never conveyed by color alone, full keyboard use.
7. Send ux-brief.md to the `ux-critic` agent for review, then fix every Blocker and Major item.
8. List anything that cannot be decided yet as questions at the end of the document. Never guess on the PO's behalf.

## Do not
- Edit files outside `docs/`.
- Add features that are not in intent.md.

## When done
Tell the human the next step is `/superbiz:spec`, which combines the intent and ux-brief into spec.md.
