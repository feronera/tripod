# Plan: Agent activity log and cost per change

References: intent.md, spec.md, ux-brief.md

## Data shape

1. **activity.log** (append-only, one `key=value` record per line, in `docs/changes/NNN-slug/`, same style as gates.log). Two record types, told apart by `event`:

   | event | fields | written by |
   |---|---|---|
   | `tool` | `at session id tool [files] [cmd]` | PostToolUse |
   | `usage` | `at session agent model input output cache_write cache_read usd seconds` | Stop, SubagentStop |

   - `id` is the tool call id. A `tool` record whose `id` is already in the file is not written again (R4).
   - `agent` is `main` or the subagent id (from `subagents/agent-<id>.jsonl`).
   - `files` holds repository-relative paths, comma-separated, or `<outside>` (R5). `cmd` is the first word of a Bash command (R3).
   - `usd` is a decimal or `unknown` (R9). `seconds` is an integer.
   - Totals are a pure fold over the records: `summary(records) -> Summary`, a typed record with sessions, tool counts, file counts, tokens by model, cost (known part, plus a list of unknown models), agent seconds, first and last time, and skipped lines. `activity.sh` and `metrics.sh` both print from this one function.

2. **docs/model-prices**: a whitespace table, one model per line: `model input output cache_write cache_read` in US$ per million tokens, and one line `as_of: YYYY-MM-DD`. Parsed into `{model: Price(input, output, cache_write, cache_read)}`. Cost = sum over the 4 token kinds of tokens × price / 1,000,000.

3. **Cursor** (`.pod/activity/<session>.json`, not committed): `{transcript_path: {"offset": bytes_read, "size": file_size}}` for the main transcript and each subagent transcript. A transcript smaller than its recorded size resets that cursor (E5). Writes to the cursor and to activity.log happen under one `fcntl` lock on `.pod/activity/.lock`, so two plugin hooks at the same Stop cannot count tokens twice (R4, R8).

4. **Active change** = `branch_change(root) -> path or None`: branch `change/NNN-slug` and folder `docs/changes/NNN-slug/` both exist, and `activity_log` in pod.yml is not `off` (R1, C4).

## Throughput checkpoint
- Blocking first steps: failing tests for R1–R16 with a recorded transcript fixture (a main transcript plus one subagent transcript), and the data shape above in `scripts/activity.py`
- Independent workstreams: docs (`docs/activity-log.md`, README, AGENTS.md) can be written apart from the code once the record format is fixed
- Shared mutable state: `scripts/lib.py` (metrics lines, gate.sh ignore warning, `activity_log` key) and both plugins' `hooks.json`
- Smallest safe decomposition: (1) parse and summarize records with tests, (2) the tool hook, (3) the usage hook with cursors, (4) activity.sh and metrics.sh, (5) gitignore and installer, (6) docs and version; each ends with `make check` passing

## Parallel parts
none: one SuperDev in the pod, and every step after the first builds on `scripts/activity.py`, so the steps run in order

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/activity.py` (new) | Records, price table, cursor, transcript reader, `hook` (reads hook JSON on stdin), `summary` | R1–R11, R13, R14 |
| `scripts/activity.sh` (new) | Wrapper: `scripts/activity.sh <change-dir>` | R11 |
| `plugins/superdev/hooks/activity.sh`, `plugins/superbiz/hooks/activity.sh` (new) | Call `python3 "$ROOT/scripts/activity.py" hook` when pod.yml and the script exist; always exit 0 | R2, R6, R13, R14, C3 |
| `plugins/superdev/hooks/hooks.json`, `plugins/superbiz/hooks/hooks.json` | Register the hook for PostToolUse (`*`), Stop and SubagentStop | R2, R6 |
| `scripts/lib.py` | `metrics` prints `agent time` and `agent cost`; `gate.sh` warns when activity.log is ignored; read `activity_log` from pod.yml | R12, R15, C4 |
| `docs/model-prices` (new) | Prices per million tokens for the current Claude models, `as_of` date, source URL in a comment | R7, C2 |
| `.gitignore`, `scripts/pod_install.py` | Add `!docs/changes/*/activity.log`; the installer copies `docs/model-prices` | R15 |
| `docs/templates/pod.yml`, `pod.yml` | `activity_log: on` with a one-line comment | C4 |
| `tests/test_activity.py` (new), `tests/fixtures/transcripts/` (new) | Tests for R1–R16 and E1–E9 | all |
| `docs/activity-log.md` (new), `README.md`, `AGENTS.md`, `docs/adopt.md` | Fields, what is never logged, price table upkeep, reading the summary, merge conflicts (E4) | R17 |
| plugin.json ×2, `.claude-plugin/marketplace.json`, `tests/test_pod_v3.py` | Version 0.7.0 | release |

## Order of work
1. Write failing tests from the requirements and edge cases in spec.md, with transcript fixtures built from the real transcript format (usage fields checked on 2026-10-09), then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. `scripts/activity.py`: records, price table, `summary`; `make test` passes for the parsing and summary tests
4. Tool hook: `hook` for PostToolUse with de-duplication, `<outside>` paths and the first command word; the plugin hook scripts and hooks.json; `make test`
5. Usage hook: transcript reader with cursors and the lock, subagent transcripts, unknown prices, failure handling; `make test`
6. `scripts/activity.sh`, the metrics lines, the gate.sh ignore warning, `activity_log: off`; `make test`
7. `.gitignore`, installer, `docs/model-prices` filled from the Anthropic pricing page; `make check`
8. Docs and version 0.7.0; `make check`, `claude plugin validate --strict` for the three manifests
9. Demo for R10: one `claude -p --output-format json` run in tripod-example on a change branch with the new hooks; compare `total_cost_usd` with `scripts/activity.sh`; record both numbers in acceptance.md

## Risks
- Transcript format changes in a later Claude Code version. Reduce: the reader takes only `message.usage`, `message.model` and `timestamp`, ignores unknown fields, and R10 shows any gap.
- Prices in `docs/model-prices` are wrong or stale. Reduce: source URL and `as_of` date in the file, the 90-day warning (C2), and the R10 comparison against Claude Code's own number.
- `claude -p` prices cache writes by cache duration (5 minutes or 1 hour), and the transcript shows them separately in `cache_creation`. Reduce: read the split when present and price each kind; if the ±5% check fails, this is the first place to look.
- A slow hook slows every tool call. Reduce: PostToolUse only appends one line (no transcript reading); transcript reading happens at Stop, incrementally; R16 test.
- The hook writes into the working tree while the agent works, so `git status` shows activity.log as changed. Reduce: the docs and the `/superdev:build` skill say to commit it with each commit; it is append-only, so it never conflicts with the agent's own edits.
- Both plugins installed: two hooks per event. Reduce: de-duplication by `id`, and the lock for usage records.

## Proof
- `make test` and `make strength` pass
- R1–R9, R11–R16: unit tests in `tests/test_activity.py`, including a privacy test that feeds a Bash command with a token-like string and asserts it is absent from activity.log (R3)
- R10: demo in tripod-example, both numbers and the difference in percent in acceptance.md
- R17: docs reviewed at gate 4
- Dogfood: from change 002 onwards, every Tripod change has activity.log (intent success measure)

## Rollback
- `git revert <merge commit>` removes the hooks, the scripts and the docs. Then run `make check` and `claude plugin validate --strict`.
- Teams on 0.7.0 can turn logging off without a release: `activity_log: off` in pod.yml.
- Existing activity.log files stay as plain text and do nothing without the scripts.

## Summary for SuperBiz
1. The agents will write down what they do in each change (which tools, which files) and how much it costs, in a file next to the gate signatures.
2. You can run one command to see a change's cost and agent time before signing a gate, and metrics will show cost per change; no prompts or command output are stored.
3. Risks: the price list must be updated by hand when prices change, and the cost check against Claude Code's own number is proven once in a demo, not continuously.
