# Intent: Simpler README and docs

Status: draft

## Problem
Tripod's README and docs grew with every release, and new readers now struggle to find the basics.

Evidence:
- The README has 337 lines.
  - It covers 11 sections, 5 command tables (25 commands) and 7 diagrams.
  - Before installing, a reader goes through concepts, modes, gates, guardrails, three layers and team setups.
  - The install commands start at line 170.
- The README repeats what the docs already say. Gates, risk tiers, merging, scaling and Autonomous mode each appear in both places, so every release has to update both. 0.8.0, 0.9.0 and 1.0.0 each needed README fixes found at review.
- The docs total about 980 lines across 11 files (excluding docs/gates.md). Several of them restate rules that the scripts already enforce and print.
- The PO asked on 2026-10-11: "Make Tripod more simple always, README should simplify too."

## Users
- New readers deciding whether to adopt Tripod, and workshop participants on their first day.
- Pod members who look up a command or a rule.
- Maintainers, who update fewer places per release.

## Success measure
- README length: from 337 lines to 130 or fewer.
  - It answers what Tripod is, the two modes, install, and one change end to end.
  - Everything else is a link.
- The first install command appears within the first 60 lines (today: line 170).
- docs/*.md, excluding docs/gates.md: from about 980 lines to 700 or fewer.
- No loss:
  - every relative link in README.md and docs/ still resolves;
  - every docs file that scripts, plugins or tests name still exists;
  - `make check` passes.

## Risk
Risk: low

1. Law or regulation: no.
2. Seen directly by customers or external users: yes, but only as documentation. No behavior changes.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches only README.md and docs/*.md, and no path in docs/risk-paths.

## Constraints
- Keep every file name in docs/: scripts, plugins and tests link to all of them. Shorten content; do not merge or rename.
- Keep governance files as they are: docs/gates.md, docs/risk-paths, AGENTS.md, CLAUDE.md. Rules move only through their own change.
- No change to scripts/, plugins/ or tests/ behavior.
- Prefer removing over adding: no new docs and no new diagrams.
- Every rule removed from a doc must still be stated somewhere, either in another doc or in the message a script prints. Duplicates go; facts stay.

## Open questions
- Which diagrams stay in the README? Proposal: the loop diagram and the two-modes diagram. The other five stay in docs/images/ and are linked from the docs that explain them.
- Removing kit features (for example parallel-check, arena or release-check) is out of scope. The spec will list candidates for a later change.
