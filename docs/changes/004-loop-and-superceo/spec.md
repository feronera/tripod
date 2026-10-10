# Spec: Loop driver and the SuperCEO agent

References: intent.md, ux-brief.md

## Requirements

Configuration
- R1: The system must read these keys from pod.yml, and `gate-check --all` must fail on a malformed value:
  - `loop: off | on` (default `off`);
  - `loop_pace_low: step | until-blocked` (default `step`);
  - `loop_max_steps` (integer, default 10), a cap on steps in one run;
  - `superceo_model` (a model id; it may equal a seat model).

  (verified by: test)

The loop
- R2: `scripts/loop.sh [--dry-run] [--change NNN]` must do one loop run. It must refuse to start, and say why, when:
  - the pod is not in `mode: autonomous`;
  - `loop` is not `on`;
  - `.pod/kill-switch` exists;
  - the working tree has uncommitted changes;
  - another loop run holds `.pod/loop.lock`.

  (verified by: test)
- R3: The next step of a change must come from one pure function, `next_step(state)`, over the change's files, gates.log and Risk. The steps, in order:

  | State | Next step | Who acts |
  |---|---|---|
  | gate 1 not complete | stop: "people sign gate 1" | people |
  | spec.md or ux-brief.md missing | draft them | SuperBiz agent |
  | gate 2 not complete | sign gate 2 | agent-sign (low) or stop for people (medium, high) |
  | plan.md missing | draft it | SuperDev agent |
  | gate 3 not complete | sign gate 3 | agent-sign (low) or stop for people |
  | no tests commit for the change | write failing tests and lock them | SuperDev agent |
  | the plan is not built | build | SuperDev agent |
  | review.md missing or older than the code | review | SuperDev agent |
  | low risk, not merged | auto-merge | `auto-merge-check --record`, then push and open the PR, with auto-merge on when `gh` is available |
  | merged, acceptance.md missing | draft acceptance | SuperBiz agent |
  | gate 4 not complete | sign gate 4 | agent-sign (low, after the auto record) or stop for people |
  | gate 4 complete | stop: "done" | nobody |

  When a gate signature was refused, the next step is "revise the artifact using the refusal reasons", by the agent that owns it. (verified by: test, one case per row)
- R4: Every drafting, building and reviewing step must run `claude -p` on the leg's seat model, with that leg's plugin (`--plugin-dir`) and the matching skill. Edits are allowed only where the step needs them: `docs/changes/NNN-slug/` for documents, plus `code_dirs` and `tests_dir` for tests and build. Shell use is limited to `make test`, `make check` and `git`. (verified by: test with a fake claude that records its arguments)
- R5: The loop must commit each step on the change's branch (`change/NNN-slug`), as `loop(NNN): <step>`, with the author `Tripod loop <loop@tripod.invalid>`, and must stop when the branch does not exist. (verified by: test)
- R6: Pace:
  - Low-risk changes take one step per run when `loop_pace_low: step`, or continue until a stop when `until-blocked`.
  - Medium and high risk take at most one step per run, and never a signing or merging step.
  - No run takes more than `loop_max_steps` steps over all changes.

  (verified by: test)
- R7: Before every step, the loop must check:
  - the kill switch;
  - the 0.9.0 stops for that change: budget, refusals, revert, forbidden paths;
  - the governance and risk-path rules of agent-sign.

  A stop ends work on that change for this run. (verified by: test)
- R8: The loop must never run `scripts/gate.sh`, `scripts/resume.sh` or `scripts/mark-revert.sh`. It must never sign gate 1. It must never merge or sign a medium or high change. (verified by: test that scans the loop's commands, and by the R3 table)
- R9: Every step and every stop must be recorded in the change's activity.log as `event=loop at run step result reason`. The digest must gain a section "loop runs: N steps, M stops (by reason)". (verified by: test)
- R10: `--dry-run` must print the step each change would take, change nothing and start no agent. (verified by: test)

SuperCEO
- R11: `scripts/superceo.sh priorities` must run `claude -p` on `superceo_model` with the superceo plugin's `priorities` skill, read-only. It must write `docs/superceo/YYYY-MM-DD.md`: open changes ranked, each with its state, next step, blocking reason, spend, and a one-line reason for its rank; plus items from `docs/backlog.md` when it exists. (verified by: test with a fake claude; demo)
- R12: `scripts/superceo.sh brief <change-dir>` must write `docs/changes/NNN-slug/brief.md` for a medium or high change that is waiting for people at a gate. The brief has the decision needed, the options, the risks, the evidence links and a recommendation. It must refuse for a low-risk change. It signs nothing. (verified by: test; demo)
- R13: The loop must call `superceo.sh brief` when a high-risk change stops at a gate that needs escalation and has no brief for the current artifact. (verified by: test)
- R14: A new plugin, `plugins/superceo`, must hold the `priorities` and `brief` skills and a read-only `superceo` agent. The marketplace must list it, and `claude plugin validate --strict` must pass. (verified by: test, validate)

CI and docs
- R15: The kit must ship `docs/templates/loop.yml`, a GitHub Actions workflow that is off until copied into `.github/workflows/`. It runs `scripts/loop.sh` and `scripts/digest.sh --write` on a schedule, with `ANTHROPIC_API_KEY` from a secret. (verified by: test that it parses and names the secret)
- R16: Demo in a copy of tripod-example with the real claude:
  - a low-risk change from gate 1 to the end of gate 4 with no step started by a person;
  - a high-risk change stopped at gate 2 with a brief;
  - a priorities file;
  - the loop stopped by a limit.

  (verified by: demo, recorded in acceptance.md)
- R17: README (roadmap step 4, the modes table, commands), docs/autonomous.md (the loop, pace, SuperCEO, CI), AGENTS.md and the pod.yml template must describe the loop and SuperCEO. (verified by: review)

## Edge cases
- E1: Empty: no open changes means the run prints "nothing to do" and records nothing. No `docs/backlog.md` means priorities cover open changes only.
- E2: Malformed: a malformed loop key fails `gate-check --all`, and loop.sh refuses with the same message. A change folder without intent.md is skipped and named in the output.
- E3: Permissions: the loop never acts as a person (R8). Its commits use its own author, so peer review at gate 4 counts the loop as a code author, not a person. Agents never edit `loop` or the limits, because pod.yml is a risk path.
- E4: Dirty tree or a missing branch: refuse (R2) or stop that change (R5), without touching files.
- E5: Two runs at once: the second refuses (`.pod/loop.lock`, R2). A stale lock (older than `loop_lock_minutes`, default 120) is reported with its age, and a person removes it.
- E6: A claude failure or timeout in a step: the step is recorded as failed, the change stops for this run, and nothing is committed.
- E7: The kill switch appears in the middle of a run: the loop stops before the next step (R7).
- E8: `gh` missing or no network at the merge step: stop with "ready to merge: push and open the PR"; the auto record stays committed.
- E9: A step's output fails `make test` (for example, the build step): record a failed result, commit nothing, and stop the change.

## Flagged concerns
- C1 (SuperDev, feasibility): the build and test steps let an agent edit code with no person watching. The defenses are those of 0.8.0 and 0.9.0: low risk only for merges, risk paths, governance files, locked tests, `make check`, review with a second model, auto-merge-check, budgets, and revert. Medium and high stop for people at every gate.
- C2 (escalation): in CI, the loop needs `ANTHROPIC_API_KEY` and a GitHub token that can push branches and open PRs. Branch protection still applies, and the token must not be an admin token. The docs say so.
- C3 (SuperBiz): SuperCEO's ranking is advice. The sponsor decides. It does not change any change's Risk or order of work by itself.
- C4: the size of this change. It is the largest so far. Proposal: build it in this order: the state machine and dry-run, then document steps, then signing, then build and review, then merge, then SuperCEO, then CI. Each part ends with `make check` passing.
- C5: it touches `scripts/**`, `plugins/**` and `.github` templates, so it is Risk: high at merge.

## Out of scope
- Writing new intents. People write intent.md; SuperCEO only ranks.
- Medium or high changes merged by the loop.
- Running several changes in parallel in one run: one change at a time, in SuperCEO's order when a priorities file exists for today, else by number.
- Stops on repeated CI failures (as in 003).
- A hosted service or dashboard.
