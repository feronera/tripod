# Intent: Simpler kit code

Status: draft

## Problem
The kit's scripts repeat the same small jobs in several places, so a fix in one copy misses the others. Changes 007 and 008 each had to find every copy of a base-branch lookup by hand.

Evidence, from a read-only survey of main at 7e5f8dd on 2026-10-13:
- **Dead code:** 17 lines that can never run, left after `return` in `lib.parse_log` by change 007.
- **Git calls:** three wrappers (`lib.git_out`, `merge_rules.git`, `loop.git`) and about 14 raw `subprocess.run(["git", …])` calls.
- **Reading a file at a ref** (`git show ref:path`) is written six times.
- **The trusted-base lookup** (`base_problem`, then `resolve_base`) is repeated at six call sites.
- **docs/risk-paths** is parsed in two places.
- **The installer's AGENTS.md "Commands" list** is a hand copy of AGENTS.md, while the other sections are already pulled from it.
- **A real bug:** `auto-merge-check.sh`, `pr-check.sh` and `parallel-check.sh --run` default `--base` to a hard-coded `main`, not pod.yml's `base_branch`. The merge skill therefore tells agents to `git fetch` and pass `--base origin/main` by hand, or a stale local main makes merged work look like part of the change.
- **The per-risk merge rules are written four times:** AGENTS.md, the gate-guard hook comment, the merge skill and docs/merge-by-risk.md.

## Users
- Maintainers of the kit, who fix one place instead of several.
- Agents running the merge skill, who get a shorter skill and a correct default base.
- Teams whose base branch is not `main`.

## Success measure
- Lines of Python in scripts/: from 4,478 to 4,350 or fewer, with no behavior change except the `--base` default.
- Places that run git: one helper in lib.py, from 3 wrappers and about 14 raw calls.
- Places that read a file at a ref: from 6 to 1. Places that decide the trusted base: from 6 to 1.
- `make check` passes; existing tests pass unchanged, except the plugin-version assertion (1.0.0 to 1.0.1), with the PO's approval.

## Risk
Risk: high

1. Law or regulation: no.
2. Seen directly by customers or external users: yes. The `--base` default changes for teams whose base is not `main`, and the merge skill text changes.
3. Rollback within minutes without data loss: yes, `git revert`.
4. Personal or sensitive data: no.

It touches `scripts/**` and `plugins/**/hooks/**`, so it is high.

## Constraints
- Prefer removing over adding: no new features, no new pod.yml keys.
- Every user-facing script name and message stays the same.
- Out of scope, by the PO's choice of scope:
  - SuperCEO's own branch scan;
  - one parser for all logs;
  - the two timestamp formats.
- Editing the merge skill bumps every plugin to 1.0.1, as the kit's version test expects them to match.

## Open questions
- none
