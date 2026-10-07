#!/usr/bin/env bash
# usage: scripts/test-strength.sh
# Flags tests that still pass when every function in app/*.py returns None.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/strength.py" "$@"
