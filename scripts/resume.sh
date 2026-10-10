#!/usr/bin/env bash
# usage: scripts/resume.sh <change-dir> "<reason>"   (people only: agent checks may run again)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/sponsor.py" resume "$@"
