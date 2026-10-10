blockers: 0
majors_open: 1
second_opinion: agree
reviewed_head: 52c3ed0fcc4d50cf3413bee8038effa9910db01b

# Review: Agent seats and agent signatures (Autonomous mode for low risk)

Three reviewer lenses on Opus 5.5 (security and governance bypass, correctness, tests and edge cases), then an independent second opinion on Sonnet 5.5 that did not see the first results.

## Blocker (all fixed)
- **B1 (security): a forged `event=mode` line made a Pod-mode repo accept agent signatures, with models of the forger's choice.** The reviewer showed auto-merge printing ALLOW. Fix: in `mode: pod` a recorded mode counts only when it is already on the base branch (a merged change), and Autonomous mode checks seats against pod.yml. Tests: ModeRecordTests.
- **R13 (correctness, tests): the PR summary part was missing, and nothing showed which gates agents signed.** Fix: `activity.sh` prints `agent gates: gate 2 owner <model>, …; refused checks: N`, counts only current signatures, and the review skill puts both lines in the PR summary. Tests: AgentGatesTests.
- **(tests) Code added after the lock had no tests:** `--tools`, the cost of refused runs, and one record per model. Fix: IsolationTests and EvidenceTests.

## Major
Fixed:
- M1: real evidence from a refused run could back a forged APPROVE. Every run now writes its verdict and cost to activity.log. A refused session, or a session already used, cannot back a signature.
- M2: a signature with no session could match usage with no session. A signature now needs both a session and a model, and agent-sign refuses when claude returns no session id.
- M3: a quoted `VERDICT: APPROVE` could flip a REFUSE. APPROVE now comes only from a single, final VERDICT line.
- M4: the checking session loaded the repo's CLAUDE.md, hooks and MCP servers. It now runs with `--safe-mode --strict-mcp-config --tools Read,Grep,Glob`; checked with the real claude.
- M6: agents could sign a change touching risk paths, and could sign gate 4 before any merge. agent-sign now refuses risk paths, and agents sign gate 4 only after an auto-merge record (gate-check enforces it too).
- Second opinion: edits to agent instructions or gate rules, committed or not, could steer the checker or weaken the rules. `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.mcp.json`, `docs/gates.md` and `docs/risk-paths` now block agent signatures, and auto-merge in either mode.
- E2, E6, R9, R11, config keys: tests added (30 in tests/test_agent_seats_review.py).

Open, for the PO at gate 4 (1):
- Deviations from the spec text, which was not amended after gate 3:
  - gate 4 is signed by agents only after an auto-merge;
  - in Pod mode, a recorded mode counts only on the base branch;
  - governance files and risk paths make agent-sign refuse;
  - every run's verdict is written to activity.log (`event=verdict`).

  All of these tighten the spec; none loosens it. Proposal: accept them as the spec.

## Minor
- A run that times out or fails before returning JSON leaves no cost record, because Claude Code returns no numbers then. Documented.
- `TRIPOD_CLAUDE` (the test override) can replace claude. Whoever can set it can also edit the files, so it falls under the accepted forgery risk. Documented.
- Nothing caps how many times agent-sign can be retried after a refusal. Refusals are counted (`refused checks: N`) for the sponsor; a cap belongs with budgets in change 003.
- The checker can read any file the user can, for example `.env`. The prompt says never to quote secrets, and it has no write or shell tools.
- ux-brief copy differences: the gate-check success line has no "agents signed N", and the not-allowed reasons are worded more precisely than in the brief.
- With `mode: pod`, a change that has an `event=mode` line now also runs `git show` on the base branch.

## Second opinion (reviewer-second)
- Sonnet 5.5, without the first results: blockers_found 0, no_blocker_verdict agree. Its two Majors (governance files, uncommitted edits) are fixed above.

## Checks
- `make check`: pass (265 tests, test-strength, CODEOWNERS, gate-check)
- `claude plugin validate --strict`: pass ×3
- Tests were locked at 2f3de62. Later test edits, all approved by the PO:
  - the auto-merge test writes pod.yml after its commit;
  - version asserts move to 0.8.0;
  - test_finished_change_keeps_its_mode merges the change first;
  - test_full_low_change_through_release adds an auto record before gate 4;
  - the new file tests/test_agent_seats_review.py.

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
