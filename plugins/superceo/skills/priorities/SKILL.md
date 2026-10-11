---
name: priorities
description: Rank the pod's open changes and backlog for the sponsor, with the state, next step, blocker, spend and a one-line reason for each rank. Read-only. Use from scripts/superceo.sh priorities, or when the sponsor asks "what next", "จัดลำดับงาน", "rank the work", "priorities".
---

# Rank the work (SuperCEO)

Goal: a ranked list the sponsor can act on in one minute. Advice only; the sponsor decides.

## Steps
1. Read each open change in `docs/changes/NNN-slug/`: intent.md (problem, success measure, Risk), gates.log (which gates are complete), activity.log (spend, refused checks, loop stops).
2. Read `docs/backlog.md` if it exists.
3. Rank by:
   - value to the intent's success measure;
   - what unblocks other work;
   - how close the change is to done;
   - cost so far.

   Put changes waiting for people first when only a person can unblock them.
4. Answer as a numbered Markdown list, one item per line: `NNN-slug: state; next step; blocker; spend US$x.xx; reason`.

## Do not
- Edit any file. The script writes your answer.
- Change any change's Risk, order of work or limits. Never sign or approve anything.
