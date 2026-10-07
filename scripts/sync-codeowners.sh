#!/usr/bin/env bash
# usage: scripts/sync-codeowners.sh [--check]
# Writes .github/CODEOWNERS from docs/risk-paths (owners: superdev_github, escalation_github).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/merge_rules.py" sync-codeowners "$@"
