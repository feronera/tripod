#!/usr/bin/env bash
# usage: scripts/mark-revert.sh <change-dir> "<reason>"   (humans only, identity = git config user.email)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" mark-revert "$@"
