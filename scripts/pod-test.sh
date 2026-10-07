#!/usr/bin/env bash
# usage: scripts/pod-test.sh
# Runs test_cmd from pod.yml. "No tests ran" (exit 5) passes only while docs/changes/ has no change.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/lib.py" test "$@"
