#!/usr/bin/env bash
# usage: scripts/superceo.sh priorities | brief <change-dir>   (SuperCEO: ranks work, briefs people; signs nothing)
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/superceo.py" "$@"
