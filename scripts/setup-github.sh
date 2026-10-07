#!/usr/bin/env bash
# usage: scripts/setup-github.sh <owner/repo> [--yes]
# Turns on repo auto-merge and protects main: required check pod-gates, code owner reviews,
# dismiss stale reviews, no force pushes. Prints the plan; applies only with --yes.
set -euo pipefail
REPO="${1:-}"
APPLY="${2:-}"
if [ -z "$REPO" ] || ! printf '%s' "$REPO" | grep -Eq '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'; then
  echo "usage: scripts/setup-github.sh <owner/repo> [--yes]" >&2
  exit 2
fi
command -v gh >/dev/null || { echo "Install gh and run gh auth login first" >&2; exit 1; }

PROTECTION='{
  "required_status_checks": { "strict": true, "contexts": ["pod-gates"] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

echo "This will configure GitHub repo $REPO as follows"
echo "  1. Turn on repo auto-merge (allow_auto_merge=true)"
echo "  2. Protect branch main"
echo "     - Require status check: pod-gates"
echo "     - Paths in docs/risk-paths need code owner review (.github/CODEOWNERS)"
echo "     - Dismiss old reviews when new commits are pushed"
echo "     - No force pushes and no deleting branch main"
echo "  Approvals by risk (SuperDev, SuperBiz, escalation) are checked by scripts/pr-check.sh in the pod-gates job"
if [ "$APPLY" != "--yes" ]; then
  echo "Nothing changed yet. Run again with --yes to apply these settings"
  exit 0
fi
gh api -X PATCH "repos/$REPO" -F allow_auto_merge=true >/dev/null
printf '%s' "$PROTECTION" | gh api -X PUT "repos/$REPO/branches/main/protection" --input - >/dev/null
echo "Done"
