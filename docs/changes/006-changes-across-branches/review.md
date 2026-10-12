blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: bbb25bd974046a170b52877b2b4361f0029bc6d4

# Review: See changes on other branches

## What changed
- `scripts/lib.py`:
  - `known_changes` lists changes from the working tree, local `change/NNN-slug` branches and remote-tracking ones, in that order, without network. A branch's gates.log and intent.md are read with `git show` into a temp folder that is always removed.
  - `open_known` applies the existing `gate_complete` to each change.
  - `cmd_new_change` uses both helpers. The refusal names where each open change is, and adds the fetch and abandoned-branch hints from ux-brief.md.
- `docs/pod-charter.md`: the WIP line.
- `open_changes` is unchanged, so `gate-check`, metrics, the digest, merge rules and SuperCEO keep their behavior (R8).

## Decision made during the build (not in the spec)
The current branch is represented by the working tree only, and a remote branch with the same name is skipped too. Without this, the usual flow (`git checkout -b change/007-x`, then `new-change.sh x`) numbered the change 008, because the folder-less branch took 007. Found by `test_working_tree_change_is_named_as_such`. Covered by that test and by `test_pushed_current_branch_keeps_its_number`.

## Second opinion (Sonnet 5.5, independent)
blockers_found 0, verdict agree.

| Finding | Severity | Outcome |
|---|---|---|
| E3 test never created a duplicate number | Major | Fixed: two live 001 branches, both named in the refusal, then numbering continues at 002 |
| Working-tree precedence test passed for the wrong reason (HEAD was skipped anyway) | Major | Fixed: the uncommitted copy on main wins over its branch |
| E4 (branch without gates.log) untested | Minor | Test added |
| Pushed current branch still took its number | Minor | Code fixed, test added |
| `change/999-x` would make the next number 1000, which `change_dirs` ignores | Minor | Open. This already happened at 999 before this change; noted for later |
| `git show` reads files whole | Minor | Accepted: gates.log and intent.md are small |

Mutation check: with the precedence rule removed, both precedence tests fail. Restored afterwards.

## Test edits (PO approved on 2026-10-12)
`tests/test_changes_across_branches.py` was locked at 963a82b. With the PO's approval, c2f36c6 fixed the two tests above and added two new ones. No other test file changed.

## Checks
- `make check`: pass (379 tests, test strength, CODEOWNERS, gate-check)
- Reproduction from intent.md: 001, 002, then refused, naming both branches
- Speed on this repository (about 20 branches): 0.11 s for `new-change.sh`

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
