# Spec: Gate 4 reads its own artifacts

References: intent.md, ux-brief.md

## Requirements
- R1: `lib.not_ready(change_dir)` must return the reasons a change's own artifacts say it is not ready (empty when ready):
  - `review.md has blockers: <N>`, when review.md exists and its `blockers:` header is not `0`;
  - `acceptance.md decides reject`, when the first word after `Decision:` in acceptance.md is `reject`, in any letter case. Agents write `Decision: reject (proposed; …)`, which counts. (Amended 2026-10-13 after the real Claude Code rehearsal showed this form.)

  (verified by: test)
- R2: `scripts/gate.sh <dir> 4` must refuse any role, before writing, when `not_ready` is not empty. The message is `Refused: gate 4 cannot be signed while the change's own artifacts say it is not ready:`, then one line per reason. (verified by: test)
- R3: `scripts/release-check.sh` must report the same reasons as problems, so the result is `NOT RELEASE-READY`. (verified by: test)
- R4: `read_review` must live in lib.py and be used by merge_rules.py, with no change to auto-merge-check's behavior. (verified by: existing auto-merge tests)
- R5: Existing tests pass unchanged. (verified by: `make check`)

## Edge cases
- E1: No review.md or no acceptance.md: no reason from that file, as today.
- E2: The template's own line `Decision: accept | reject`, left unedited: not a reject.
- E3: `blockers:` missing from review.md: not a reason. auto-merge-check already refuses it on its own path.

## Flagged concerns
- none

## Out of scope
- Checking `second_opinion`, or test results, at gate 4. CI and auto-merge-check already cover them.
