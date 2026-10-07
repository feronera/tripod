# Credits

## pstack

Several of the engineering methods in this kit are adapted from pstack by Lauren Tan
(https://github.com/cursor/plugins/tree/main/pstack), published under the MIT License.
Copyright (c) 2026 Lauren Tan

This kit does not copy pstack's text. It rewrites the ideas to fit a two-person pod and its gates,
and turns the important ones into checks enforced by scripts, hooks or CI.

| Idea from pstack | How the pod uses it |
|---|---|
| Foundational thinking, model the domain (data shape before logic) | The `## Data shape` section in plan.md, checked at gate 3 |
| Throughput checkpoint from poteto-mode | The `## Throughput checkpoint` section in plan.md, checked at gate 3 |
| Separate before serializing shared state | `## Parallel parts` with non-overlapping files, checked at gate 3 |
| Sequence work into verifiable units | The `/superdev:build` skill: one unit, one commit with passing tests |
| Test behavior, not implementation (tests that still pass when every function returns an empty value) | `scripts/test-strength.sh` in `make check`, and the 5 kinds of weak test in `/superdev:test-first` |
| Fix root causes | The `/superdev:bug-fix` skill |
| An opinion from another model (cross-model review) | The `reviewer-second` agent and `second_opinion` in review.md |
| Arena (several approaches in parallel, then choose) | The `/superdev:arena` skill, with the locked tests as the judge |
| Encode lessons in structure | The rule in `docs/pod-charter.md`: a rule broken twice must become a hook, script or CI check |

The governance layer (gates, cross-approval, risk tiers, the WIP limit, the audit log in gates.log and merge by risk)
is original to this kit.
