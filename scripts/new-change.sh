#!/usr/bin/env bash
# usage: scripts/new-change.sh <slug>   (refuses when WIP limit is reached)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" new-change "$@"
