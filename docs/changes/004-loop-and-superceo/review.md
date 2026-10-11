blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: e3b9bce9855cd2db9a515ac2cbed31d55ef1cdf1

# Review: Loop driver and the SuperCEO agent

Reviewed three times. Each review used reviewer lenses on Opus 5.5 and an independent second opinion on Sonnet 5.5.

## Round 1 (the first, larger version): led to the scope cut
- Security found 4 Blockers:
  - agents could rewrite gates.log and activity.log;
  - the loop ran the branch's own checkers;
  - access tokens reached agent-written code;
  - user settings widened agent permissions.
- Correctness found 1 Blocker (the demo did not reach the success measure) and 10 Majors.
- Tests found 1 Blocker (R13 untested) and 6 Majors.
- The PO cut the scope to the document stages on 2026-10-11 (spec.md, plan.md amended; gates 2 and 3 signed again; tests/test_loop.py replaced with approval).

## Round 2 (amended code)
- Security found 2 Blockers, both fixed:
  - a branch could name itself as base_branch and run its own scripts;
  - the brief path skipped the checks.

  The fix is the rule that the loop works only on branches whose changes are all inside their own docs/changes/NNN-slug/ folder. It reads its rules once, before any checkout, and refuses a change/* base. Tests: BranchRuleTests.
- Majors, all fixed:
  - a rollback could delete a person's ignored file (RunTests);
  - failed git commands were ignored;
  - SuperCEO was not isolated (SecretTests);
  - secrets other than tokens reached agents (SecretTests);
  - the kill switch in the middle of a run and a branch without a folder had no tests (RunTests);
  - README lines were out of date;
  - the R15 demo had no priorities file or digest (demo/final).

## Round 3 (second opinion, Sonnet 5.5, without the earlier results)
- blockers_found 0, no_blocker_verdict agree.
- Its Majors are fixed:
  - links in the change folder now stop the loop (EdgeTests);
  - R14 validate: `claude plugin validate --strict` passes for the marketplace and all three plugins, as recorded under Checks.
- Its Minors are fixed:
  - odd `loop_max_steps` values;
  - dry run shows the same stops;
  - the lock is released on error;
  - the autonomous.md wording.
- Its Read-scope Minor is documented as an accepted limit: agents can read what the user running the loop can read.

## Minor (open)
- Agents' Read tool is not limited to the repository (documented in "Limits you accept").
- `superceo_model` is not validated; empty falls back to the SuperBiz seat model.
- Copy differs slightly from ux-brief.md (empty-state wording, no model in the loading line).
- tests/test_pod_v3.py version asserts were moved to 1.0.0 with superceo (approved with the first test-lock edits).

## Checks
- `make check`: pass (364 tests, test-strength, CODEOWNERS, gate-check)
- `claude plugin validate --strict`: pass for the marketplace and for superbiz, superdev and superceo
- Tests locked at 27fabf7 (the replacement test_loop.py). Later test files are tests/test_loop_review.py (new, approved).

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
