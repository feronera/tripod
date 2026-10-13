blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: 65ec62966cd4682eddbfaccc3f02b3ec3ed8cf5f

# Review: Gate 4 reads its own artifacts

## Checks against the spec
| Req | Result |
|---|---|
| R1 `not_ready` | review.md `blockers` other than `0`; acceptance.md's decision `reject`, using the last `Decision:` line and its first word, any letter case, markdown bold or backticks allowed |
| R2 gate.sh 4 | Refuses every role before writing, with one line per reason |
| R3 release-check | Reports the same reasons. All ten earlier changes in this repository are still RELEASE-READY |
| R4 `read_review` moved | Pure move to lib.py; merge_rules uses `lib.read_review`. The auto-merge tests are unchanged and pass |
| R5 existing tests | Unchanged; `make check` passes (424 tests) |

## Rehearsal with real Claude Code (the evidence for the intent)
- **Before** (kit 1.0.6, US$1.72): the review agent wrote `blockers: 1`, and acceptance wrote `Decision: reject`. Gate 4 was signed anyway, and release-check said RELEASE-READY.
- **After** (this branch, US$2.71, git commit allowed):
  - the build finished, and `make test` passed 34 of 34;
  - the review found a real Blocker: test-strength flagged a weak test that the test-first agent wrote;
  - gate 4 was refused for both people, and release-check said NOT RELEASE-READY.
- That run showed agents write `Decision: reject (proposed; SuperBiz to confirm)`. R1 was amended to read the first word, and a test was added with the PO's approval.

## Second opinion (Sonnet 5.5, independent)
- blockers_found 0, verdict agree.
- 4 of the 6 new tests fail on main.
- The refusal sits before any write and applies to every role. Post-merge acceptance and bootstrap are not blocked.

| Finding | Severity | Outcome |
|---|---|---|
| M3: `Decision: **reject**`, `**Decision:** reject`, backticks and trailing punctuation were missed | Minor | Fixed. Checked by calling `not_ready` directly on 11 cases, all correct. No locked test was edited, so these cases have no automated test |
| M1: only the first Decision line counted, so a draft accept followed by a final reject slipped through | Minor | Fixed: the last Decision line counts. Checked the same way |
| M2: a quoted example `Decision: reject` as the last Decision line would refuse | Minor | Accepted: rare, and it fails closed |
| M4: `blockers: none` or an empty value refuses | Minor | Accepted: it matches auto-merge-check, and the message shows the value |

## Test edits (PO approved on 2026-10-13)
- `tests/test_gate4_artifacts.py` is new and locked.
- `tests/test_gate4_artifacts_review.py` is new (the Decision line with more words).

## Gates
The PO asked the agent to run every signature for this change ("Yes, do it all"). Gate 2 was signed again after the R1 amendment.

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
