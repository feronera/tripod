# Spec: See changes on other branches

References: intent.md, ux-brief.md

## Requirements

Known changes
- R1: The system must list the known changes as a set of names (`NNN-slug`), with this precedence when a name appears in more than one place:
  1. folders in the working tree's `docs/changes/`;
  2. local branches `change/NNN-slug`;
  3. remote-tracking branches `<remote>/change/NNN-slug`, as last fetched.

  It must not use the network. A branch name that does not match `change/NNN-slug` is ignored. (verified by: test)
- R2: For a change known only from a branch, its state must be read from that branch's tip: `docs/changes/<name>/gates.log` and `intent.md`, read with `git show`, without checking out. A branch with no such folder still counts for numbering (R3), but not as open (R4). (verified by: test)

Numbering
- R3: `scripts/new-change.sh <slug>` must number the new change one above the highest number among all known changes (R1), whether or not their gate 1 is signed. (verified by: test)

WIP limit
- R4: A change is open when gate 1 is complete and gate 4 is not, using the same loose test as today (`gate_complete`), applied to the files from R1 and R2. (verified by: test)
- R5: `new-change.sh` must refuse when the open changes (R4), across the working tree and all branches, reach `wip_limit`. The refusal must name each open change and where it was found (working tree, or the branch name). (verified by: test)
- R6: A change whose gate 4 is complete does not count as open, even if its branch still exists after the merge. (verified by: test)

No other change
- R7: Output on success is unchanged: one line, the new folder path. The usage line and the exit codes (0 created, 1 refused, 2 usage) are unchanged. (verified by: test)
- R8: Other commands that list changes keep their behavior: `gate-check --all`, metrics, the sponsor's digest, merge rules and SuperCEO. Only `new-change.sh` reads branches. (verified by: `make check` with existing tests unchanged)

## Edge cases
- E1: Not a git repository, or git is missing: fall back to the working tree only, as today, with no error. (verified by: test)
- E2: The same name on a local and a remote branch with different gates.log contents: the local branch wins (R1 order).
- E3: Two branches already share a number (an old collision): both count toward WIP if open, and numbering continues above both.
- E4: A branch's gates.log or intent.md cannot be read (deleted on that branch): treat it as not open.
- E5: An abandoned branch with gate 1 signed and no gate 4 counts as open until someone deletes the branch. The refusal message says how.
- E6: Remote branches are only as fresh as the last `git fetch`. The refusal message mentions `git fetch` when any change came from a remote branch.

## Flagged concerns
- The precedence in R1 means the working-tree copy of the current change wins over its own branch tip. The working tree may have unsaved signatures that are not yet committed. This matches what `gate-check` sees today.
- Existing WIP tests build changes in the working tree only, so they keep passing. New tests cover branches. No locked test needs to change. (The intent allowed WIP test edits, but none is needed.)

## Out of scope
- Warning about existing duplicate numbers in `gate-check --all`.
- Fetching from the network.
- Changing which commands other than `new-change.sh` read branches.
