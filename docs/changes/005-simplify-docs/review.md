blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: 4bc9d4b7c972ec3179d67e48ee1aa51c19cdaaef

# Review: Simpler README and docs

## Checks against the spec
| Req | Result |
|---|---|
| R1 README ≤ 130 lines | 107 (was 337) |
| R2 sections in order | What Tripod is (the intro, no heading), Install, A change end to end, Two modes, Learn more, Built with Tripod, License and credits |
| R3 first install command ≤ line 60 | line 24 (was 146; the intent's "170" was the Getting started heading) |
| R4 two diagrams in README; five moved | adlc-loop and modes in README. hitl-hotl in autonomous.md, risk-lanes in merge-by-risk.md, setup-2/3/n in scaling.md |
| R5 commands | Every command from the old README is described in a doc, or in the end-to-end table (new-change.sh, gate.sh).  moved to adopt.md |
| R6 docs ≤ 700 lines (excluding gates.md) | 694. Baseline correction: the intent's "about 980" wrongly included gates.md; the true baseline was 904 |
| R7 referenced docs exist | All. The grep also finds  and , which are a test fixture and SuperCEO's optional input, not kit docs |
| R8 topics referrers expect | bootstrap and peer review (scaling), price table (activity-log), 5 kinds (test-strength), Limits you accept (autonomous), 9 conditions (merge-by-risk), trust ladder (pod-charter): all present |
| R9 no lost facts | See below |
| R10 links and anchors | Link check passed (relative links, images and anchors in README.md and docs/*.md) |
| R11 only README and docs |  README.md                                  | 324 +++++------------------------
 docs/activity-log.md                       |  22 +-
 docs/adopt.md                              | 215 +++++++------------
 docs/autonomous.md                         | 104 ++++-----
 docs/changes/005-simplify-docs/gates.log   |   6 +
 docs/changes/005-simplify-docs/intent.md   |  52 +++++
 docs/changes/005-simplify-docs/plan.md     |  73 +++++++
 docs/changes/005-simplify-docs/spec.md     |  64 ++++++
 docs/changes/005-simplify-docs/ux-brief.md |  45 ++++
 docs/merge-by-risk.md                      |  73 ++-----
 docs/parallel-agents.md                    |  64 ++----
 docs/pod-charter.md                        |   6 +-
 docs/scaling.md                            |  90 +++-----
 docs/test-strength.md                      |  20 +-
 14 files changed, 479 insertions(+), 679 deletions(-) lists README.md and 8 docs, plus this folder. scripts/pod-test.sh
pod-test: python3 -m unittest discover -s tests -t . -v
scripts/test-strength.sh
test-strength: checked 6 tests, no weak tests
scripts/sync-codeowners.sh --check
CODEOWNERS matches docs/risk-paths
scripts/gate-check.sh --all
Warning: bootstrap: on. 1945996+feronera@users.noreply.github.com also holds escalation, so Risk: high changes get no independent escalation check. Turn bootstrap off when a third person joins (docs/scaling.md).
OK   001-agent-activity-log (passed up to gate 4 merge-ready, Risk: high)
OK   002-agent-seats (passed up to gate 4 merge-ready, Risk: high)
OK   003-sponsor-controls (passed up to gate 4 merge-ready, Risk: high)
OK   004-loop-and-superceo (passed up to gate 4 merge-ready, Risk: high)
OK   005-simplify-docs (passed up to gate 3, Risk: low) passes (364 tests) |

## R9: facts moved or restored
- README guardrails: risk tiers (risk-tiers.md), stale approvals (gates.md), WIP (pod-charter.md, now naming the new-change refusal), locked tests (gates.md, parallel-agents.md), verified identity (merge-by-risk.md GitHub setup), kill switch (README Two modes, pod-charter.md).
- README plugin table: moved to adopt.md step 4, with superceo added.
- README safety model: README Two modes (3 bullets) and autonomous.md. ".pod/ is never committed" and "sample data is invented" were restored in adopt.md.
- README status: "several SuperDevs not yet run with real teams" in scaling.md. "No stop on repeated CI failures" added to Limits you accept.
- README three layers and engineering methods: credits.md.
- README repository layout: dropped. It described this repository only, which GitHub shows.
- adopt.md installed-files table: dropped. The installer prints every file and the skipped ones.
- Fixed while shortening (stale facts):
  - adopt.md said the repository is private (public since 2026-10-09);
  - activity-log.md and scaling.md called Autonomous mode and SuperCEO "planned".

## Second opinion (Sonnet 5.5, independent)
- blockers_found 0, verdict agree.
- Fixed:
  - the default of 10 for ;
  - the CI-failure caveat;
  - Node  detection;
  - the  agent.
- Left as is:
  -  lines (the installer adds them);
  - the engineering-method list (in credits.md).

## Code authors
None: documentation only.
