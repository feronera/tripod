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
command -v gh >/dev/null || { echo "ต้องติดตั้ง gh และ gh auth login ก่อน" >&2; exit 1; }

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

echo "จะตั้งค่า GitHub repo $REPO ดังนี้"
echo "  1. เปิด auto-merge ของ repo (allow_auto_merge=true)"
echo "  2. ป้องกัน branch main"
echo "     - ต้องผ่าน status check: pod-gates"
echo "     - path ใน docs/risk-paths ต้องได้ review จาก code owner (.github/CODEOWNERS)"
echo "     - review เก่าถูกยกเลิกเมื่อมี commit ใหม่"
echo "     - ห้าม force push และห้ามลบ branch main"
echo "  การอนุมัติตาม risk (SuperDev, SuperBiz, escalation) ตรวจโดย scripts/pr-check.sh ใน job pod-gates"
if [ "$APPLY" != "--yes" ]; then
  echo "ยังไม่ได้เปลี่ยนอะไร รันอีกครั้งพร้อม --yes เพื่อใช้ค่าตามนี้"
  exit 0
fi
gh api -X PATCH "repos/$REPO" -F allow_auto_merge=true >/dev/null
printf '%s' "$PROTECTION" | gh api -X PUT "repos/$REPO/branches/main/protection" --input - >/dev/null
echo "ตั้งค่าเรียบร้อย"
