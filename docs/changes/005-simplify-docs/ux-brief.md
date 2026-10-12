# UX brief: Simpler README and docs

References: intent.md

The readers are:
- a new reader deciding whether to adopt Tripod (on GitHub, often on a phone);
- a workshop participant on day one;
- a pod member looking up a rule.

They read on github.com, in the rendered Markdown view.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| README.md | Decide and start in five minutes | what Tripod is, install, one change end to end, two modes, links | Install |
| docs/*.md | Look up one topic in depth | one topic per file, rules first, examples after | Apply the rule |

## README outline (target lines)
| Section | Content | Lines |
|---|---|---|
| What Tripod is | Badges. One paragraph covering the three legs, four gates, two modes and that scripts enforce the rules. The loop diagram | 12 |
| Install | Requirements line, new project, existing project, plugins (marketplace and `--plugin-dir`), protect main. Link to docs/adopt.md | 35 |
| A change, end to end | The 8-step table with commands and gates. The defect, arena and incident skills in one line. Link to tripod-example | 22 |
| Two modes | The modes diagram. A 4-row table (who signs, where the person is, high risk, status). Safety in three bullets. Link to docs/autonomous.md | 22 |
| Learn more | One line per doc: gates, risk tiers, merge by risk, scaling, autonomous, activity log, test strength, parallel agents, pod charter, adopt | 14 |
| Built with Tripod | This repository is a pod. `make check` before a PR. Releases link for status | 6 |
| License and credits | MIT; pstack credit; link to docs/credits.md | 5 |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| README.md | Not applicable | Not applicable | A broken link or image (prevented by R10) | The reader installs without scrolling past concepts |
| docs/*.md | Not applicable | Not applicable | A topic the reader expects has moved: a one-line pointer names the new place | The rule is in the first screen of the doc |

## Copy
| key | Text | Notes |
|---|---|---|
| tagline | **An agentic delivery practice.** Three agent legs (SuperBiz, SuperDev and SuperCEO) run every change through four gates, and scripts, hooks and CI enforce the rules | First line under the badges |
| learn_more | Each topic has one doc. Scripts link to these docs in their messages | Lead-in of Learn more |
| pointer | Moved to [docs/<file>](<file>) | Where a section was removed |

## Accessibility notes
- Every image keeps a full alt text that says what the diagram shows.
- Tables have at most 4 columns in the README, so they fit a phone screen.
- Headings are sentence case and unique within a file, so anchor links stay stable.
