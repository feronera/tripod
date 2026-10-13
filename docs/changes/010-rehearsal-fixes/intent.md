# Intent: Fixes from the lab rehearsal

Status: draft

## Problem
A full rehearsal of the pod deck's Labs 0 to 9 on Tripod 1.0.5, on 2026-10-13, found three problems in the kit. Each would trip up pairs in the workshop.

Evidence (rehearsal script and output kept in the session scratchpad; summary below):
- **Signatures not shared.** `scripts/gate.sh` prints only `Recorded: gate N role=… by=…`. Nothing says the signature exists only on this machine. Pairs work on two machines, so the other person never sees the signature and cannot sign the cross-check: `gate.sh` refuses until the owner has signed the current artifact.
- **Compiled files committed.** The installer's `.gitignore` lines do not cover `__pycache__/`. After `make test`, the deck's `git add -A` committed `app/__pycache__/history.cpython-314.pyc`. auto-merge-check then counted 210 changed lines for a 9-line change, and refused it as over `auto_merge_max_lines` (200).
- **A repeat signature passes silently.** When one person signed gate 1 of a change twice, `gate.sh` recorded a second owner line and printed "gate 1 is not complete". It said nothing about why the second signature did not count. Lab 3 promises a refusal here.

## Users
- Workshop pairs, from Lab 1 onward.
- Every pod whose members work on separate machines.
- Python projects installed with the kit.

## Success measure
In the rehearsal script, without the stand-in steps that fixed these by hand:
- Signatures pushed after each gate: the kit tells the signer how, on every `Recorded` line. Today: no hint.
- auto-merge-check's line count for the 9-line change in Lab 7: from 210 to 9.
- A second signature by the same person, for the same gate and current artifact: refused with a message. Today: recorded silently.
- `make check` passes; existing tests unchanged.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Every team sees the new `gate.sh` lines and the new `.gitignore` line.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**`, so it is high.

## Constraints
- Small: two messages and one `.gitignore` line. No new pod.yml keys and no new commands.
- `gate.sh` still never runs git commands itself. It only prints the next step.

## Open questions
- none
