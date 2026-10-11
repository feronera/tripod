# Plan: Loop driver and the SuperCEO agent

References: intent.md, spec.md (scope amended 2026-10-11)

## Data shape
- `State(change, risk, gate1, spec, gate2, plan, gate3, refused)`, read from the change folder by `read_state`. `refused[n]` is true when the last agent check of gate n refused it, and its artifact has not changed since.
- `Step(kind, name, actor)` from a pure `next_step(state)`, following the six rows of the spec table. Kinds: draft, sign, stop.
- Each step names the artifact files it may write: `draft spec` writes spec.md and ux-brief.md, `draft plan` writes plan.md. Everything else in the repository is read-only for the agent.

## Throughput checkpoint
- Blocking first steps: rewrite tests/test_loop.py for the amended spec (failing first), with the PO's approval to replace the locked file
- Independent workstreams: the docs; the superceo script and plugin are already built and only need their tests kept
- Shared mutable state: scripts/loop.py (removing the build, merge and CI parts, adding the isolation and pre-step checks)
- Smallest safe decomposition: (1) remove the cut parts, (2) isolate agent sessions and limit edits to artifacts, (3) checks before every step, (4) brief at gate 2, (5) docs; each ends with `make check`

## Parallel parts
none: one SuperDev, one file at the centre (scripts/loop.py)

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/loop.py` | the six-row table; isolated sessions; artifact-only edits; checks before each step (risk paths from the base branch, governance, forbidden, stops); atomic lock; records; dry-run; brief at gate 2 | R1–R10, R13 |
| `scripts/superceo.py`, `plugins/superceo/` | kept as built | R11, R12, R14 |
| `scripts/sponsor.py` | loop section and the refusal default (kept) | R1, R9 |
| `scripts/agent_sign.py` | prompt lines on gates already verified (kept, now in the spec) | R4 |
| `docs/templates/loop.yml` | removed | out of scope |
| `docs/autonomous.md`, README, AGENTS.md, `docs/templates/pod.yml` | short sections | R16 |
| `tests/test_loop.py` | rewritten for the amended spec | all |

## Order of work
1. Write the failing tests for the amended spec, then commit (replacing the locked file, with the PO's approval)
2. Lock the tests
3. Steps (1) to (5) above, each ending with `make check`
4. Demo in a copy of tripod-example: a low-risk change to "people build", a high-risk change to gate 2 with a brief, a priorities file

## Risks
- Agent sessions need the plugin's skills without user settings: checked on 2026-10-11 (`--setting-sources ""` with `--plugin-dir` loads the skills and gives no shell).
- An artifact can still carry misleading text into later steps (spec C1): two models check gates 2 and 3, and people start the build.

## Proof
- `make test` and `make strength` pass
- R1–R14: tests/test_loop.py with a fake claude
- R15: demo in acceptance.md

## Rollback
- `git revert <merge commit>`, or `loop: off`.

## Summary for SuperBiz
1. The loop now writes the spec and plan and gets them checked by two agents on different models. When the plan is approved, it stops and hands the build to people.
2. SuperCEO ranks the work every day and writes a brief whenever a high-risk change waits for a decision.
3. Risks: the automatic build and merge were cut, to keep Tripod simple and safe. People still start each build.
