#!/usr/bin/env bash
# usage: scripts/gate-check.sh <change-dir> [upto]
#        scripts/gate-check.sh --all
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" check "$@"
