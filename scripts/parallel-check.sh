#!/usr/bin/env bash
# usage: scripts/parallel-check.sh <change-dir> [--run [--base <ref>]]
# Before splitting a change into parallel worktrees: each part's tests must exist and must not import
# files that another part builds, so every part can go green on its own.
# --run (after the build, before merging): run each part's tests in a throwaway worktree where the other
# parts' files are put back to how they are at the merge base. A failure shows a real dependency.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" parallel-check "$@"
