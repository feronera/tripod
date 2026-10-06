#!/usr/bin/env bash
# usage: scripts/gate.sh <change-dir> <1|2|3|4>   (identity = git config user.email)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" gate "$@"
