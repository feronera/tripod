# Intent: See changes on other branches

Status: draft

## Problem
`scripts/new-change.sh` decides two things from the current working tree only: the next change number, and whether the WIP limit is reached. Each change lives on its own `change/NNN-slug` branch until it merges, so open changes are mostly on other branches.

Evidence:
- **Reproduced on 2026-10-12** in a fresh repository with Tripod 1.0.1 and `wip_limit: 2`. Three changes were started from main, each on its own `change/*` branch with gate 1 signed. They were all numbered `001`, and none was refused.
- **Numbering collides.** Two people who start a change from main at the same time both get the same number.
- **The WIP limit is almost never enforced.** On main, every change in `docs/changes/` has passed gate 4, so `new-change.sh` counts 0 open changes. On a change branch it sees only that change. The README, pod-charter.md and scaling.md all promise the limit.
- SuperCEO and the loop already read `change/*` branches, so the kit has a pattern for this.

## Users
- Pod members starting a change.
- SuperBiz, who relies on the WIP limit so that review does not queue (scaling.md).
- The sponsor and SuperCEO, who read the same open-change list.

## Success measure
In a test repository with two open changes on `change/*` branches (gate 1 signed, gate 4 not) and `wip_limit: 2`:
- `new-change.sh` refuses to start a third change. Today it accepts. Target: refused, naming both branches.
- The next number is above every number on a local or remote-tracking `change/NNN-*` branch. Today two branches can share a number. Target: no collision, for branches the machine has fetched.
- Changes already merged, or with gate 4 complete, do not count as open, even when their branch still exists.
- `make check` passes; no existing test changes its expected result except the WIP tests that encode the bug, with the PO's approval.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. Every team running `new-change.sh` sees new refusals that were silently skipped before.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**`, which `docs/risk-paths` makes high.

## Constraints
- Python 3 stdlib and git only. No network: remote branches are what was last fetched, and the message says so.
- `new-change.sh` keeps its usage and output. Only new refusal text is added.
- Keep it small: reuse the branch listing that SuperCEO and the loop already use, rather than adding a new mechanism.

## Open questions
- Should a remote branch with no gate 1 signature (an intent still being drafted) take a number? Proposal: yes for numbering, no for WIP.
- Should `gate-check --all` also warn when two branches share a number? Proposal: no, to keep the change small; the new numbering prevents new collisions.
