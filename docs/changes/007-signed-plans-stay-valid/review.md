blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: 141a9f5a1a4198d769e71f0e0f7f1bfd7f1c2f84

# Review: Signed plans stay valid after a kit upgrade

## What changed
- `scripts/lib.py`:
  - `plan_merged_as_is` returns True only when the base branch holds this change's plan.md with the same blob and a gate 3 signature for that blob from every required role. `check_gate` skips `check_plan` only then. `cmd_gate` still runs `check_plan` before every signature (R3).
  - `ci_base_ref` reads the pull request's real base from the GitHub event payload, or from `GITHUB_BASE_REF`.
  - `parse_log` was split out of `read_log` so both read gates.log the same way.
- `docs/adopt.md`: one line in "Update the kit from upstream" about `gate-check --all` and `bootstrap: on` (R5).

## Spec amendment before the code
The first R1 trusted any signed plan, which would have broken `PlanCheckTests.assert_refused`: a hand-written signature on a bad plan must still fail. R1 was amended to trust only plans already on the base branch, and gates 2 and 3 were signed again.

## Second opinion (Sonnet 5.5, independent)
- First run: blockers_found 0, with one Major and three Minors. The reviewer disagreed with going to gate 4 until the Major was fixed. The fixes below address it.

| Finding | Severity | Outcome |
|---|---|---|
| A PR could set `base_branch` to its own branch (CI fetches every branch), so a forged signature skipped the check. Confirmed by experiment | Major | Fixed: a `change/*` base is never trusted, and in CI the base must equal the PR's real base (event payload, else `GITHUB_BASE_REF`). Tests: `BaseRedirectTests` |
| The base log was parsed with `split()`, so a `#` comment or quoted text could count as a signature | Minor | Fixed: shared `parse_log`. Test: `BaseLogParsingTests` |
| Base-side signatures are not checked for `by` or agent validity | Minor | Accepted: the working-tree role loop still checks them (R4) |
| Missing tests: origin/main preference, partial base log with a working-tree signature | Minor | Open. The origin/main path is the same `resolve_base` used by peer review today |

Found while fixing: on a push event `GITHUB_BASE_REF` is empty, and on `pull_request_review` it is not set at all. `ci_base_ref` reads the event payload, which has `pull_request.base.ref` for both PR events, and treats an empty value as unset. This was checked by hand with a `pull_request_review` payload; there is no automated test for the payload path.

## Open (not in this change)
- `mode_record_on_base` (change 002) trusts `base_branch` from pod.yml the same way. It needs the same guard in a later change.
- A branch numbered 999 still makes the next number 1000 (from change 006).

## Test edits (PO approved on 2026-10-13)
- `tests/test_signed_plans.py` was locked at 69cc35f and is unchanged.
- `tests/test_signed_plans_review.py` is new: a7985d2, then a01843a, which imports the module so the locked tests do not run twice.

## Checks
- `make check`: pass (391 tests, test strength, CODEOWNERS, gate-check)
- tripod-example, upgraded with this branch's kit and `bootstrap: on`: 001, 002 and 003 pass `gate-check --all` (003 failed before)

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
