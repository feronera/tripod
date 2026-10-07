#!/usr/bin/env bash
# usage: scripts/test-strength.sh
# Mode from pod.yml `strength`: python flags tests that still pass when every function under
# code_dirs returns None; off prints a notice; cmd runs strength_cmd. See docs/test-strength.md.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/strength.py" "$@"
