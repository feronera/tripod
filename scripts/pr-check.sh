#!/usr/bin/env bash
# usage (CI):    scripts/pr-check.sh            (reads the PR via gh api: GH_TOKEN, GITHUB_REPOSITORY, GITHUB_EVENT_PATH)
# usage (local): scripts/pr-check.sh --author <login> --approvals <login,login> --base <ref>
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/merge_rules.py" pr-check "$@"
