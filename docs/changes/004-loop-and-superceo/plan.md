# Plan: Loop driver and the SuperCEO agent

References: intent.md, spec.md, ux-brief.md

## Data shape

1. **The state of a change** is one typed record, read from its files:
   `State(change, risk, branch_exists, has: {spec, ux_brief, plan, tests, build, review, acceptance, brief}, gates: {1..4: complete?}, refused: {gate: reasons}, auto: bool, merged: bool)`.
   - `tests` is a commit on the branch that touches `tests_dir`.
   - `build` is a code commit after it.
   - `review` is review.md whose `reviewed_head` is still current (the 002 rule).
   - `merged` is an auto record whose head is on the base branch.

   `read_state(change_dir, cfg) -> State` is the only place that reads files or git.

2. **The step table** is data, not code: an ordered list of
   `Rule(name, applies(state) -> bool, step, actor, kinds: draft | sign | build | merge | stop)`.
   `next_step(state, cfg) -> Step | Stop` takes the first rule that applies, then applies the Risk rules: medium and high turn `sign` and `merge` into a stop for people. It is pure, so every row of the spec's table is one test.

3. **A step** is `Step(name, actor_leg, skill, allowed_edit_paths, allowed_bash, model)`, built from the table plus pod.yml. Running it is a single function, `run_step(step, state) -> Result(ok, committed, reason, session)`:
   - drafting, building and reviewing call `claude -p`;
   - signing calls `agent_sign.main`;
   - merging calls `merge_rules` plus `git push` and `gh`.

4. **A run** is a loop over changes in priority order: today's `docs/superceo/YYYY-MM-DD.md` when it exists, else by number. Pace and `loop_max_steps` bound it. Every step and stop appends `event=loop` to the change's activity.log through one `record()` function.

## Throughput checkpoint
- Blocking first steps:
  - failing tests for the step table (one per row), the refusals to start, pace, the cap and the records, using fake `claude`, `gh` and `git push`;
  - `State`, `Rule` and `next_step` in `scripts/loop.py`.
- Independent workstreams:
  - the superceo plugin (skills, agent, manifest) and `scripts/superceo.py` once `read_state` exists;
  - the CI template and the docs.
- Shared mutable state: `scripts/loop.py` and the digest section in `scripts/sponsor.py`. The marketplace manifest is shared with the superceo plugin.
- Smallest safe decomposition (C4 of the spec); each part ends with `make check`:
  1. state, the table and `--dry-run`;
  2. drafting steps;
  3. signing steps;
  4. tests, build and review steps;
  5. the merge step;
  6. records and the digest section;
  7. SuperCEO;
  8. CI template and docs.

## Parallel parts
none: one SuperDev, and every part builds on `read_state` and `next_step` in scripts/loop.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/loop.py` (new), `scripts/loop.sh` (new) | config, refusals, lock, State, the table, next_step, run_step, pace, records, dry-run | R1–R10, R13 |
| `scripts/superceo.py` (new), `scripts/superceo.sh` (new) | priorities and brief; read-only claude runs; files written by the script, not the agent | R11, R12 |
| `plugins/superceo/` (new: `.claude-plugin/plugin.json`, `skills/priorities/SKILL.md`, `skills/brief/SKILL.md`, `agents/superceo.md`) | the third leg as a plugin | R14 |
| `.claude-plugin/marketplace.json` | list superceo | R14 |
| `scripts/sponsor.py` | digest section "loop runs" | R9 |
| `scripts/lib.py` | `gate-check --all` reports loop key problems | R1 |
| `docs/templates/loop.yml` (new), `docs/templates/pod.yml` | the CI example, off; the loop keys | R15, R1 |
| `scripts/pod_install.py` | copy the template; `--vendor-plugins` includes superceo | R15, R14 |
| `docs/autonomous.md`, README, AGENTS.md | the loop, pace, SuperCEO, CI and token advice | R17 |
| `tests/test_loop.py` (new) | all requirements and edge cases with fakes | all |
| plugin.json ×3, marketplace.json, `tests/test_pod_v3.py` version asserts | 1.0.0: Autonomous mode is complete (that test edit needs PO approval while tests are locked) | release |

## Order of work
1. Write failing tests from the requirements and edge cases (fake `claude`, fake `gh`, a bare git remote for push), then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. Part 1: state, table, dry-run; `make check`
4. Part 2: drafting steps; `make check`
5. Part 3: signing steps (agent-sign, revise after a refusal); `make check`
6. Part 4: tests, build, review steps (`make test` must pass before a commit); `make check`
7. Part 5: merge step (auto-merge-check, push, PR, auto-merge; stop when gh is missing); `make check`
8. Part 6: records and the digest section; `make check`
9. Part 7: the SuperCEO plugin and superceo.py; the loop calls brief; `make check` and `claude plugin validate --strict` ×4
10. Part 8: CI template, installer, docs, version; `make check`
11. Demo in a copy of tripod-example with the real claude (R16): a low-risk change from gate 1 to the end of gate 4 by `loop.sh` alone; a high-risk change that stops at gate 2 with a brief; a priorities file; a limit that stops the loop. Record it in acceptance.md

## Risks
- The agent in the build step changes more than it should. Reduce:
  - edits are limited by path (`--allowedTools Edit(...)`, `Write(...)`) and Bash is limited to `make test`, `make check` and `git`;
  - `--tools` keeps other tools out;
  - `make test` must pass before a commit;
  - review and auto-merge-check follow.
- A loop that never ends or keeps spending. Reduce: `loop_max_steps`, the 0.9.0 budgets and refusal stops, and the kill switch checked before every step.
- Branch and git state confusion: the loop works on the current checkout. Reduce:
  - refuse a dirty tree;
  - switch to `change/NNN-slug` and back;
  - never force-push;
  - a lock file.
- Real runs are slow and cost money. Reduce: tests use fakes; the demo uses small changes and low budgets.
- The superceo plugin breaks marketplace validation. Reduce: validate in every part that touches manifests.

## Proof
- `make test` and `make strength` pass
- R1–R15: unit tests in tests/test_loop.py with fakes
- R16: demo recorded in acceptance.md (gates.log, activity.log, loop output, priorities file, brief)
- R17: docs reviewed at gate 4

## Rollback
- `git revert <merge commit>`; then `make check` and plugin validation.
- Without a release: `loop: off` in pod.yml, or the kill switch. Every step the loop took is a normal commit on a change branch, and can be reverted like any other.

## Summary for SuperBiz
1. A loop moves low-risk work from an approved intent to a merged and accepted change on its own, one step at a time or until it is blocked. It stops at every gate where people must decide.
2. A SuperCEO agent ranks the open work every day and writes a short brief whenever a high-risk change needs a decision from people. It signs nothing.
3. Risks: agents now write and merge code with no person starting each step. The limits, review, auto-merge checks, budgets, kill switch and revert from earlier releases are the safety net, and the demo tests them on real work.
