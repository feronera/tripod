# UX brief: Simpler kit code

References: intent.md

The users are pod members and agents running the kit's scripts and the merge skill. Output text does not change, apart from one new DENY reason.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/auto-merge-check.sh <dir>` | Decide an automated merge | ALLOW, or DENY with reasons, as today | Merge, or fix the reasons |
| `/superdev:merge` skill | Merge by risk | shorter steps: run auto-merge-check without `--base`; rules in docs/merge-by-risk.md | Follow the steps |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| auto-merge-check | As today | Not applicable | DENY, adding the base problem as a reason when the base cannot be trusted | ALLOW, as today |

## Copy
| key | Text | Notes |
|---|---|---|
| base_reason | `<base problem from change 008>` | One DENY reason line, only when `base_problem` is not None |
| rules_pointer | The merge rules for each risk are in docs/merge-by-risk.md. | AGENTS.md, gate-guard hook comment, merge skill |

## Accessibility notes
- No change to output format.
