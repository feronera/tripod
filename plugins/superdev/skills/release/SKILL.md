---
name: release
description: Prepare a release once the change is release-ready (scripts/release-check.sh). Run the release checklist, write rollback steps and a runbook entry in docs/changes/NNN-slug/runbook.md, and run a kill-switch drill. Use when the user says "ปล่อยงาน", "release", "deploy", "เตรียม release", "runbook".
---

# Release (SuperDev: Deploy and MA)

Goal: a release that can be rolled back, with a runbook the operators can use afterwards.

## Steps
1. Check that it is ready to release: `scripts/release-check.sh docs/changes/NNN-slug`.
   - Release-ready means gate 4 has both SuperDev (owner) and SuperBiz (acceptance), and neither is stale.
     A high-risk change also needs escalation, and the change must have no revert record.
   - A low-risk change that was auto-merged still cannot go to production until SuperBiz accepts it.
   - If it fails, give the human every message line and stop.
2. Release checklist:
   - [ ] `make check` passes on the latest branch
   - [ ] CI (pod-gates) passes
   - [ ] acceptance.md says `accept`
   - [ ] The Rollback in plan.md has been rehearsed at least once
   - [ ] No personal data or secrets in the diff
3. Write `docs/changes/NNN-slug/runbook.md`:
   - What changed (one paragraph)
   - How to check the system works normally after release
   - Symptoms to watch for, and which logs to read
   - Rollback steps, one command at a time, for example `git revert <commit>` then `make check`
   - Contacts: SuperDev and escalation from pod.yml
4. Kill-switch drill:
   1. Ask the human to run `touch .pod/kill-switch`.
   2. Call a tool once, and confirm the hook refuses it with the message "kill switch is on".
   3. Stop all work, and wait for the human to run `rm .pod/kill-switch` themselves.
   4. Record the drill result in runbook.md.
5. Merging into main goes through `/superdev:merge` and must pass the gate-guard hook. Never work around the hook.
6. If the change must be rolled back after release, a human runs `scripts/mark-revert.sh docs/changes/NNN-slug "<reason>"`.
   This record makes release-check fail, and the pod must rebuild its track record before auto-merge.

## Do not
- Delete `.pod/kill-switch` yourself.
- Run `scripts/mark-revert.sh` yourself. It is a human decision.
- Release when acceptance.md says `reject`.

## When done
Tell the human the next step is for SuperBiz to use `/superbiz:release-notes`.
