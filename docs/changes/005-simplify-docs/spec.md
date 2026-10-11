# Spec: Simpler README and docs

References: intent.md, ux-brief.md

## Requirements

README
- R1: README.md must be 130 lines or fewer. (verified by: `wc -l`)
- R2: README.md must contain these sections, in this order, and no others:
  1. What Tripod is
  2. Install
  3. A change, end to end
  4. Two modes
  5. Learn more
  6. Built with Tripod
  7. License and credits

  The sections are described in ux-brief.md. (verified by: review against ux-brief.md)
- R3: The first install command (`git clone https://github.com/feronera/tripod ~/tripod`) must appear within the first 60 lines of README.md. (verified by: `grep -n`)
- R4: README.md must show at most two diagrams: the loop (`docs/images/adlc-loop.svg`) and the two modes (`docs/images/modes.svg`). Each of the other five diagrams must be shown in the doc that explains its topic:
  - `hitl-hotl.svg`: docs/autonomous.md
  - `risk-lanes.svg`: docs/merge-by-risk.md
  - `setup-2.svg`, `setup-3.svg`, `setup-n.svg`: docs/scaling.md

  (verified by: `grep` for each image)
- R5: README.md must list commands only in "A change, end to end". Every command it no longer lists must still be described in at least one file in docs/. (verified by: a check, run at review, of each of the 25 commands in today's README)

Docs
- R6: The docs/*.md files, excluding docs/gates.md, must total 700 lines or fewer (today: 982). (verified by: `wc -l`)
- R7: Every file in docs/ that scripts/, plugins/, tests/, AGENTS.md or docs/templates/ names must still exist, with the same name. (verified by: `make check`, plus a check at review)
- R8: Each doc must still cover the topic its referrers point to. Examples:
  - bootstrap and peer review in docs/scaling.md;
  - updating the price table in docs/activity-log.md;
  - the weak test patterns in docs/test-strength.md;
  - "Limits you accept" in docs/autonomous.md;
  - the 9 auto-merge conditions in docs/merge-by-risk.md.

  (verified by: review, listing each reference found with `grep -rn "docs/<name>.md"`)
- R9: Every rule removed from a doc must still be stated in another doc, or in the message the script that enforces it prints. Duplicate text goes; facts stay. (verified by: review of the diff, with a list of removed facts and where each now lives)
- R10: Every relative link and image in README.md and docs/*.md must resolve to an existing file. Anchor links must match an existing heading. (verified by: a link check run at review)

No behavior change
- R11: The change must touch only README.md, docs/*.md (excluding docs/gates.md) and its own change folder. `make check` must pass. (verified by: `git diff --stat main`, `make check`)

## Edge cases
- E1: A fact appears in the README only (for example the requirements line: Python 3.10, git, make, Claude Code). It must stay in the README's Install section, or move to docs/adopt.md.
- E2: A doc section that a script message names by its title (for example "Limits you accept") must keep that title, so the reader can find it.
- E3: A doc links to a README anchor that no longer exists (for example `README.md#two-modes`). The link must be updated to an anchor that exists, or point to the doc instead.
- E4: GitHub renders relative links from the repository root. Links in docs/ must stay relative to docs/.

## Flagged concerns
- docs/adopt.md (192 lines) overlaps the README's install steps and docs/pod-charter.md (the trust ladder). The plan must decide where each topic lives, and say so in a one-line pointer from the other place.
- docs/autonomous.md was rewritten in 1.0.0. Shortening it must not drop any line of "Limits you accept": those are the risks the sponsor accepts.

## Out of scope
- docs/gates.md, docs/risk-paths, AGENTS.md and CLAUDE.md (governance files).
- scripts/, plugins/ (including skill text) and tests/.
- New docs, new diagrams, translations.
- Removing kit features. Candidates for a later change (to be confirmed by usage):
  - `scripts/parallel-check.sh` and docs/parallel-agents.md;
  - the `arena` skill;
  - `scripts/release-check.sh` (overlaps gate 4 release-ready);
  - `scripts/metrics.sh` (overlaps `scripts/activity.sh`);
  - `--vendor-plugins`.
