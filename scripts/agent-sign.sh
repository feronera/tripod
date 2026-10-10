#!/usr/bin/env bash
# usage: scripts/agent-sign.sh <change-dir> <2|3|4>   (an agent signs one seat, Autonomous mode only)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/agent_sign.py" "$@"
