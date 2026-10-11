#!/usr/bin/env bash
# usage: scripts/loop.sh [--dry-run] [--change NNN]   (one loop run, Autonomous mode)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/loop.py" "$@"
