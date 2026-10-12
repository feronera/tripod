# Plan: See changes on other branches

References: intent.md, spec.md, ux-brief.md

## Data shape
- `known_changes(root)` returns a dict mapping each name (`NNN-slug`) to `(where, files)`:
  - `where` is `working tree`, `branch change/NNN-slug` or `branch <remote>/change/NNN-slug`;
  - `files` is a path to a folder holding that change's `gates.log` and `intent.md`.
    - For the working tree, it is the real folder.
    - For a branch, it is a temporary folder filled with `git show <ref>:docs/changes/<name>/<file>`. A file that is missing on the branch is left out.
- The dict is filled in R1 order (working tree, local, remote), and an existing name is never replaced.
- `open_changes` keeps its signature for the other callers (R8). `new-change` uses a new `open_known(cfg, known)`, which applies `gate_complete(files, 1/4, cfg)` to each entry.

## Throughput checkpoint
- Blocking first steps: failing tests for R1 to R7 and E1 to E6 in a new `tests/test_changes_across_branches.py`, then lock.
- Independent workstreams: none. One function and one command.
- Shared mutable state: `scripts/lib.py` (`cmd_new_change`, plus two new helpers next to `open_changes`).
- Smallest safe decomposition: four steps, each ending with `make check`: (1) `known_changes` (R1, R2, E1, E2, E4); (2) numbering (R3, E3); (3) WIP (R4 to R6, E5, E6, the copy); (4) docs

## Parallel parts
none: one function in one file

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | `known_changes`, `open_known`; `cmd_new_change` uses them. Branches are listed with `git for-each-ref refs/heads/change/ refs/remotes/`, filtered to `<remote>/change/NNN-slug`, the same way as `loop.py` and `superceo.py` | R1–R7 |
| `tests/test_changes_across_branches.py` | new: branches made in a temp repo, plus a bare "remote" cloned and fetched | all |
| `docs/pod-charter.md` | the WIP line: counts open changes on every branch, as last fetched | R5 |

The temporary folders are created under `tempfile.mkdtemp()` and removed in a `finally`.

## Order of work
1. Write the failing tests, commit, `touch .pod/lock-tests`.
2. Steps 1 to 4 above, each ending with `make check`.
3. Re-run the reproduction from intent.md (three changes from main, `wip_limit: 2`). Expected: 001, 002, then a refusal.

## Risks
- Speed: one `git show` per file per branch. A pod has few open branches, and `for-each-ref` is one call. Measure it in the repro with the Tripod repository's 20 or so branches; the target is under 1 second.
- An abandoned branch blocks new work (E5). This is intended, and the message says how to free the slot.
- Remote branches with a name in another format (`origin/HEAD`) are filtered out by the `change/NNN-slug` pattern.

## Proof
- `make test` and `make strength` pass.
- R1 to R7, E1 to E6: the new test file.
- Success measure: the repro, recorded in acceptance.md.

## Rollback
- `git revert <merge commit>`. No data or format changes.

## Summary for SuperBiz
1. New changes get a number no other branch already holds, so two people starting at once no longer collide.
2. The WIP limit now counts open changes on every branch, so it works as the README and charter promise.
3. Risks: an abandoned branch keeps a WIP slot until someone deletes it, and the refusal says how.
