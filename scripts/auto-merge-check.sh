#!/usr/bin/env bash
# usage: scripts/auto-merge-check.sh <change-dir> [--base main] [--record]
# Prints ALLOW or DENY with reasons. --record appends a gate=4 role=auto line on ALLOW.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/merge_rules.py" auto-merge-check "$@"
