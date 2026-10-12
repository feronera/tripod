# Plan: Simpler README and docs

References: intent.md, spec.md, ux-brief.md

## Data shape
- A **fact** is one rule, command, setting or limit. Each fact has exactly one home doc. Other places get a one-line pointer, or nothing.
- **Home of each topic.** This resolves the flagged concern about adopt.md:

  | Topic | Home | Elsewhere |
  |---|---|---|
  | Install commands, requirements, plugins | README Install | adopt.md links to it |
  | Installer options, installed files, installer rules, configure, update from upstream | adopt.md | none |
  | Fit assessment, pilot, 30/60/90 measures, checklist | adopt.md | none |
  | Auto-merge trust ladder | pod-charter.md (the team fills it in) | adopt.md and merge-by-risk.md: one-line pointer |
  | Several people per role, bootstrap, peer review, splitting, setup diagrams | scaling.md | pod-charter.md: pointer |
  | Who merges at each tier, the 9 conditions, revert, the risk-lanes diagram | merge-by-risk.md | none |
  | Autonomous mode, sponsor, loop, SuperCEO, Limits you accept, the hitl-hotl diagram | autonomous.md | README Two modes: summary and link |
  | Guardrails and three layers (today in the README) | gates.md (unchanged), risk-tiers.md, credits.md | README Learn more |
  | Commands not in "A change, end to end" | the doc of their topic (R5 table at review) | none |

## Throughput checkpoint
- Blocking first steps: none. There are no tests to write first, because this change has no behavior. R1 to R11 are checked by commands at review.
- Independent workstreams: README; adopt.md and pod-charter.md; autonomous.md; the other docs.
- Shared mutable state: the topic table above. Every file follows it.
- Smallest safe decomposition: one commit per file group. Each ends with the link check and `make check`.

## Parallel parts
none: one SuperDev. The files are small, and the fact table must stay consistent across them.

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `README.md` | Rewrite to the ux-brief outline. Two diagrams. Commands only in the end-to-end table | R1–R5 |
| `docs/adopt.md` (192 → ~120) | Install points to the README. The trust ladder points to pod-charter. Remove the duplicated plugin steps. Fix "The repository is private" (public since 0.5.x). Shorten the installed-files table | R6, R8, R9 |
| `docs/autonomous.md` (170 → ~125) | Remove text repeated from the README and merge-by-risk. Keep every line of "Limits you accept". Add the hitl-hotl diagram | R4, R6, R8 |
| `docs/scaling.md` (99 → ~70) | Shorten. Add the three setup diagrams | R4, R6, R8 |
| `docs/merge-by-risk.md` (92 → ~70) | Shorten. Add the risk-lanes diagram. The trust ladder points to pod-charter | R4, R6, R8 |
| `docs/parallel-agents.md` (94 → ~65) | Shorten the worked example | R6 |
| `docs/activity-log.md` (85 → ~65) | Shorten; keep fields, privacy and the price-table steps | R6, R8 |
| `docs/test-strength.md` (64 → ~50) | Shorten; keep the 5 kinds | R6, R8 |
| `docs/pod-charter.md` (57 → ~50) | Who-reviews-whom points to scaling | R6 |
| `docs/risk-tiers.md`, `docs/credits.md` | Unchanged unless a pointer is needed | R10 |

Target total: about 690 lines, below the 700 limit.

## Order of work
1. Record the baseline:
   - the 25 commands in today's README, and where each is documented;
   - `grep -rn "docs/<name>.md"` for every doc (R8);
   - the line counts.
2. README (R1–R5). Then the link check and `make check`.
3. adopt.md and pod-charter.md. Then the checks.
4. autonomous.md. Then the checks.
5. scaling.md, merge-by-risk.md, parallel-agents.md, activity-log.md and test-strength.md. Then the checks.
6. The review lists each removed fact and where it now lives (R9).

## Risks
- A fact silently disappears while shortening (R9). Mitigation: per-file review of the diff, plus the removed-facts list in review.md.
- Script messages name a doc section, and it is renamed (E2). Mitigation: `grep` the scripts for quoted section titles before renaming any heading.
- External links to README anchors (the workshop deck links only to the repository root, checked on 2026-10-11).

## Proof
- R1, R3, R6: `wc -l` and `grep -n`.
- R4, R5, R7, R8, R10: a link and reference check script, run at review from the scratchpad. It is not added to the kit.
- R11: `git diff --stat main` and `make check`.

## Rollback
- `git revert <merge commit>`.

## Summary for SuperBiz
1. The README becomes a short front page: what Tripod is, how to install it, one change end to end, and the two modes. Everything else is one link away.
2. Each topic lives in one doc, so the next release updates one place instead of two.
3. Risks: a rule could be dropped while shortening. Review lists every removed fact and where it now lives.
