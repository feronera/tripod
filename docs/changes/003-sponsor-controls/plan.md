# Plan: Sponsor controls (budget, ceiling, automatic stops, daily digest)

References: intent.md, spec.md, ux-brief.md

## Data shape

1. **Limits** come from pod.yml once, into one typed record:
   `Limits(per_change: float|None, per_day: float|None, max_refusals: int|None, merges_per_day: int|None, forbidden: tuple[str, ...])`.
   `read_limits(cfg) -> (Limits, problems)`. A missing key is `None` (no limit). A malformed or negative value is a problem string, so `gate-check --all` and agent-sign report the same text.

2. **The ledger** is a list of dated events read from the logs that already exist. Nothing new is stored, except the `event=resume` line in gates.log.
   `Event(at: datetime UTC, change: str, kind: str, data: dict)`. Kinds:
   - `usage`: activity.log; has `usd`, `model`, `session`, `source`;
   - `verdict`: activity.log; has `gate`, `verdict`;
   - `signature`: gates.log; a person or an agent;
   - `auto`: gates.log `role=auto`;
   - `revert`: gates.log `event=revert`;
   - `resume`: gates.log `event=resume`.

   `ledger(root) -> (events, skipped)` reads every change once. Spend, stops and the digest are all pure functions over it, so the numbers in the digest and in a refusal cannot disagree:
   - `spend(events, change=None, since=None) -> (usd, unknown_count)`;
   - `estimate(events, now) -> usd`: the most expensive agent-sign run (usage summed per session, `source=agent-sign`) in the last 7 days;
   - `stops(events, limits, change, gate, now) -> [reason]`: budget, refusals in a row, revert;
   - `digest(events, limits, now, hours) -> text`.

3. **"Since a person last acted"** for a change is the latest `at` of any signature by a person, or of any `event=resume`. The refusals counted are `verdict=refuse` events for that gate after that time.

## Throughput checkpoint
- Blocking first steps: failing tests for R1–R12 and E1–E8, with gates.log and activity.log fixtures and fixed clocks; the `Limits` and `Event` shapes in `scripts/sponsor.py`
- Independent workstreams: docs (autonomous.md, README, AGENTS.md, template) once the keys and copy are fixed; the demo once the stops work
- Shared mutable state: `scripts/agent_sign.py` (calls the stops), `scripts/merge_rules.py` (forbidden paths, merges per day), `scripts/activity.py` (hook warning) and `scripts/lib.py` (config check), each with a small hook into sponsor.py
- Smallest safe decomposition: (1) limits and ledger, (2) spend and stops, (3) agent-sign and auto-merge wiring, (4) hook warning, (5) resume.sh, (6) digest.sh, (7) docs and version; each ends with `make check` passing

## Parallel parts
none: one SuperDev, and every step builds on sponsor.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/sponsor.py` (new) | Limits, ledger, spend, estimate, stops, digest, resume; CLI `digest` and `resume` | R1, R3–R7, R11, R12 |
| `scripts/digest.sh`, `scripts/resume.sh` (new) | Wrappers | R7, R11, R12 |
| `scripts/agent_sign.py` | Before starting an agent: the stops for this change and gate, and forbidden paths | R2, R4–R6, R8 |
| `scripts/merge_rules.py` | auto-merge DENY for forbidden paths and for merges per day | R8, R9 |
| `scripts/activity.py` | PostToolUse: when a budget is reached, print `hookSpecificOutput.additionalContext` once per session per limit (marker in `.pod/activity/`) | R10 |
| `scripts/lib.py` | `gate-check --all` reports `read_limits` problems | R1 |
| `docs/templates/pod.yml` | commented limit keys | R14 |
| `docs/autonomous.md`, README, AGENTS.md | the sponsor's controls, digest, resume; agents never run resume.sh | R14 |
| `tests/test_sponsor.py` (new) | all requirements and edge cases | all |
| plugin.json ×2, marketplace.json, `tests/test_pod_v3.py` version asserts | 0.9.0 (that test edit needs PO approval while tests are locked) | release |

## Order of work
1. Write failing tests from the requirements and edge cases (fixture logs, a fixed `now` through an env var `TRIPOD_NOW` read only by sponsor.py, and the fake claude from change 002), then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. `sponsor.py`: limits, ledger, spend, estimate, stops; `make test`
4. Wire agent-sign and auto-merge-check; `make test`
5. The hook warning; `make test`
6. `resume.sh` and `digest.sh`; `make test`
7. Docs, template and version 0.9.0; `make check` and `claude plugin validate --strict` ×3
8. Demo in a copy of tripod-example with the real claude: a small budget, `max_refusals_per_gate: 2` with a planted defect, a forbidden path, then the digest compared with the logs; record it in acceptance.md

## Risks
- The hook warning depends on Claude Code's PostToolUse `additionalContext` output. Reduce: the hook prints valid JSON only when there is a warning, and a test checks the JSON shape; the demo shows the message reaching the agent.
- Reading every change's logs on each agent-sign and each tool call. Reduce: the hook reads only when a budget key is set, and only the current change plus the day's window; R16 of change 001 (under 100 ms) must still pass.
- Clock handling. Reduce: all times converted to UTC; tests use a fixed `TRIPOD_NOW`.
- The estimate can be low (C1, accepted). Reduce: the digest shows spend against the limit.

## Proof
- `make test` and `make strength` pass
- R1–R12: unit tests in tests/test_sponsor.py (fixed clock, fixture logs, fake claude)
- R13: demo recorded in acceptance.md
- R14: docs reviewed at gate 4

## Rollback
- `git revert <merge commit>`; then `make check` and plugin validation.
- Without a release, remove the limit keys from pod.yml: every control turns off.

## Summary for SuperBiz
1. The sponsor can set a spending limit per change and per day, a cap on how many changes agents merge per day, and paths agents may not touch; agents stop on their own when they hit a limit, after repeated refusals, or after a revert.
2. A daily digest shows what the agents did and spent in the last 24 hours, from the same records the stops use.
3. Risks: a single run can still go slightly over budget because a running session is never cut off, and a person must run resume after repeated refusals.
