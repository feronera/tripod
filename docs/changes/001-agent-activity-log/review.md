blockers: 0
majors_open: 1
second_opinion: agree
reviewed_head: 1190531d255084569110f9e7ac2834a7d88d7b84

# Review: Agent activity log and cost per change

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.
Reviewed by three reviewer lenses (security, correctness, tests and edge cases) on Opus 5.5, then an independent second opinion on Sonnet 5.5 that did not see the first results.

## Blocker
- scripts/activity.py first_word: when `shlex` could not parse a command (an unbalanced quote), the fallback split could log the second half of a quoted `VAR="secret value"` as `cmd` (R3, secrets in logs) -> fixed: an unparseable command is logged as `cmd=?`, and only a plain program name is accepted. Test: test_activity_review.PrivacyTests.test_unparseable_command_logs_no_part_of_a_secret.

## Major
Fixed:
- format_record: a value with a newline (for example a file name) could forge a usage record and inflate cost (R7, R11, R12) -> control characters are replaced. Test: test_newline_in_a_value_cannot_forge_a_record.
- tool_record: MCP tools with a `path` argument had it logged as a file, which can hold personal data (R3, E7) -> only built-in file tools contribute paths. Test: test_mcp_tool_path_is_not_logged.
- Usage on a non-change branch was charged to the next change after a branch switch (E3, E8) -> the read position moves on even when nothing is recorded. Tests: BranchSwitchTests.
- A missing transcript left no record (E5) -> recorded as `tokens=unknown`; a rewritten transcript keeps the counted message ids. Tests: TranscriptProblemTests.
- A missing price table printed the wrong copy (E6) -> `cost: unknown (docs/model-prices not found)`. Test: test_missing_price_table.
- SessionEnd and the hook registration had no test -> SessionEndTests, test_hooks_registered_for_every_event_in_both_plugins.

Open, for the PO at gate 4 (1):
- The implementation goes slightly beyond the spec text, and spec.md and plan.md were not amended after gate 3 (amending them would make gates 2 and 3 stale):
  - a `SessionEnd` hook, added because Claude Code writes a session's last response after the Stop hook (found in the R10 demo: -3.6% before, -1.3% after);
  - one usage record per transcript and model, not one per turn;
  - an extra field, `cache_write_1h`, needed to price one-hour cache writes.
  All three are described in docs/activity-log.md. Proposal: accept them as the spec at gate 4.

## Minor
- Agent time also leaves out idle time before a person's prompt (found in review), so the turn time is the sum of active gaps.
- The lock waits at most 2 s, the cursor is saved atomically, and a damaged cursor skips to the end of the transcript (tokens may be missed, never counted twice).
- `--resume` or `--fork-session` may copy earlier history into a new session file, which would be counted again. Not checked on Claude Code 2.1.291; documented as a follow-up.
- Without a `tool_use_id`, a tool call is written once per installed plugin. Claude Code always sends it today.
- R16 measures the hook's own cost over a bare bash + python start (median about 30 ms here). The raw median is about 50 ms, also under 100 ms.
- Both plugins run the project's `scripts/activity.py` on every tool call (as gate-guard already does with gate-check.sh). docs/activity-log.md should say so for people opening untrusted repositories: follow-up.
- Symlinked `.pod/activity` or change folders are followed. A hostile repository can already run code through the hooks, so this adds little; follow-up.
- hooks.json entries were reformatted to multi-line.
- `import activity` inside lib.cmd_metrics avoids a circular import.

## Second opinion (reviewer-second)
- Sonnet 5.5, without the first results: blockers_found 0, no_blocker_verdict agree.
- Its Majors are the spec-text deviations listed under "Open" above, plus E4 (merge conflicts) covered by test_two_sessions_and_conflict_markers.

## Checks
- `make check`: pass (202 tests, CODEOWNERS, gate-check)
- `scripts/test-strength.sh`: pass
- `claude plugin validate --strict`: pass for the marketplace and both plugins
- Tests locked at 9cc6274. Later test changes, all approved by the PO: 4 lines in tests/test_pod_v3.py (gitignore lines, version 0.7.0) and the new tests/test_activity_review.py (21 tests).

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
