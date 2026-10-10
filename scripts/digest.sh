#!/usr/bin/env bash
# usage: scripts/digest.sh [--hours N] [--write]   (the sponsor's view of the last N hours)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/sponsor.py" digest "$@"
