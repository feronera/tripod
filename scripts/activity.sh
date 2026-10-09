#!/usr/bin/env bash
# usage: scripts/activity.sh <change-dir>   (what the agents did in a change and what it cost)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/activity.py" summary "$@"
