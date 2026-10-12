# Acceptance: Simpler README and docs

References: intent.md, spec.md

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| README from 337 to ≤ 130 lines | `wc -l README.md` | 107 | Yes |
| First install command within 60 lines | `grep -n "git clone https://github.com/feronera/tripod" README.md` | line 24 | Yes |
| docs/*.md (excluding gates.md) ≤ 700 lines | `wc -l` | 694 (true baseline 904, not 980) | Yes |
| No loss: links resolve, referenced docs exist, `make check` passes | link check, reference grep, `make check` | all pass; second opinion found no lost fact that matters | Yes |

## Demo steps
1. Open README.md on GitHub.
   - Expected: install is on the first screen after the intro and diagram, and every doc is one link away.
   - Actual: as expected.
2. Follow each Learn more link.
   - Expected: each doc opens with its rule first.
   - Actual: as expected.

## Decision
Decision: accept (proposed by the agent; SuperBiz confirms by signing gate 4)

Reason: every target was met with no behavior change. Each topic now has one home, so the next release updates one place.

Next: a separate change to remove the kit features listed under Out of scope in spec.md, after checking how they are used.
