#!/usr/bin/env bash
# usage: scripts/parallel-check.sh <change-dir>
# Before splitting a change into parallel worktrees: each part's tests must exist and must not import
# files that another part builds, so every part can go green on its own.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" parallel-check "$@"
