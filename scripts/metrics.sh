#!/usr/bin/env bash
# usage: scripts/metrics.sh <change-dir>
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" metrics "$@"
