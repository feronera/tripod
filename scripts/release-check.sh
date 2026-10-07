#!/usr/bin/env bash
# usage: scripts/release-check.sh <change-dir>
# release-ready = gate 4 owner + cross (SuperBiz acceptance) fresh, + escalation for high, no revert
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" release-check "$@"
