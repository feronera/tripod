# Spec: Loop driver and the SuperCEO agent

References: intent.md, ux-brief.md

Scope amended on 2026-10-11 by the PO, after review. The loop does the document stages only: it drafts spec and plan and signs gates 2 and 3. People start the build. The automatic build, tests, merge and the CI template are cut; three reviews found that running agent-written code and merging unattended needed many more safeguards. That conflicts with keeping Tripod simple. The cut also covers the intent's success measure: the loop now covers the steps from gate 1 to the end of gate 3.

## Requirements

Configuration
- R1: The system must read `loop: off | on` (default `off`), `loop_max_steps` (integer of 1 or more, default 10) and `superceo_model` (a model id) from pod.yml. `gate-check --all` must fail on a malformed value. With `loop: on`, `max_refusals_per_gate` defaults to 3. (verified by: test)

The loop
- R2: `scripts/loop.sh [--dry-run] [--change NNN-slug]` must do one loop run. It must refuse to start, and say why, when:
  - the pod is not in `mode: autonomous`;
  - `loop` is not `on`;
  - `.pod/kill-switch` exists;
  - the working tree has uncommitted changes;
  - another run holds `.pod/loop.lock` (created atomically).

  (verified by: test)
- R3: The next step of a change must come from one pure function over its state:

  | State | Next step | Who |
  |---|---|---|
  | gate 1 not complete | stop: people sign gate 1 | people |
  | no spec.md | draft spec.md and ux-brief.md | SuperBiz agent |
  | gate 2 not complete | low: revise the spec if the last check refused it, else sign gate 2; medium or high: stop for people | agents or people |
  | no plan.md | draft plan.md | SuperDev agent |
  | gate 3 not complete | low: revise the plan if refused, else sign gate 3; medium or high: stop for people | agents or people |
  | otherwise | stop: people build (gate 3 is complete) | people |

  (verified by: test, one case per row)
- R4: Agent steps run `claude -p` on the leg's seat model with the leg's plugin, in an isolated session:
  - `--setting-sources ""` and `--strict-mcp-config`, so no user or project settings, hooks or MCP servers apply;
  - no shell, tools limited to `Read,Grep,Glob,Skill,Edit,Write`;
  - edits allowed only to the step's own artifact files (spec.md and ux-brief.md, or plan.md);
  - access tokens such as `GH_TOKEN`, `GITHUB_TOKEN` and `*_TOKEN` removed from the environment.

  (verified by: test)
- R5: After a step, the loop must check every file changed since the step began, committed or not. Anything other than the step's artifacts rolls the branch back to where the step started. The loop commits the step as `Tripod loop <loop@tripod.invalid>` with git hooks off. (verified by: test)
- R6: Before every step the loop must check:
  - the kill switch;
  - the sponsor's stops for that change and gate;
  - that the branch, committed or not, touches no path in the base branch's docs/risk-paths, no governance file and no `agent_forbidden_paths`.

  So a branch never runs checkers it changed. (verified by: test)
- R7: Pace: one step per change per run, and at most `loop_max_steps` steps per run over all changes. (verified by: test)
- R8: The loop never runs people's commands, never signs gate 1, never signs medium or high risk, and never builds, tests, pushes or merges. (verified by: test and by the R3 table)
- R9: Every step and stop is recorded as `event=loop` in the change's activity.log. A stop that repeats the last record is not recorded again. The digest's "loop runs" section counts steps and stops. (verified by: test)
- R10: `--dry-run` prints each change's next step and changes nothing. (verified by: test)

SuperCEO
- R11: `scripts/superceo.sh priorities` writes `docs/superceo/YYYY-MM-DD.md`, ranking the open changes, including those on `change/*` branches with their intent's problem and success measure, plus `docs/backlog.md`. It runs on `superceo_model`, read-only, with the skill text in the prompt. (verified by: test with a fake claude; demo)
- R12: `scripts/superceo.sh brief <change-dir>` writes brief.md for a medium or high change waiting at a gate, and refuses for low risk. It signs nothing. (verified by: test; demo)
- R13: When a high-risk change stops for people at gate 2 and has no brief for the current artifact, the loop asks SuperCEO for one and commits it. (verified by: test)
- R14: The superceo plugin (priorities and brief skills, a read-only agent) is in the marketplace and passes `claude plugin validate --strict`. (verified by: test, validate)

Demo and docs
- R15: Demo in a copy of tripod-example with the real claude:
  - a low-risk change goes from gate 1 to "people build" with no step started by a person;
  - a high-risk change stops at gate 2 with a brief;
  - a priorities file.

  (verified by: demo)
- R16: docs/autonomous.md, README, AGENTS.md and the pod.yml template describe the loop and SuperCEO in a few lines each. (verified by: review)

## Edge cases
- E1: No open change branches: "Loop: nothing to do".
- E2: Malformed keys: `gate-check --all` fails, and loop.sh refuses with the same message.
- E3: The loop's commits use its own author; the plugin's activity hook may append to activity.log, and nothing else outside the artifact files is accepted.
- E4: Dirty tree: refuse to start. A branch with no change folder: skipped and named.
- E5: Two runs at once: the second refuses; the lock shows its age.
- E6: claude fails or times out: the step is recorded as failed and nothing of the agent's is kept.
- E7: The kill switch appears in the middle of a run: the loop stops before the next step.

## Flagged concerns
- C1: an agent-written spec or plan can still steer later agents through its content. The checks at gates 2 and 3, on two different models, and people at the build step are the defense.
- C2: a run that is not on a schedule needs a person or cron to start it. The kit ships no CI template; teams that add one must give it a token that triggers checks, and must not give agents that token.
- C3: it touches `scripts/**` and `plugins/**`, so it is Risk: high at merge.

## Out of scope
- The automatic build, tests, review, merge, acceptance and gate 4 (people start the build with `/superdev:test-first`).
- A CI workflow template.
- Writing intents; ranking is advice only.
