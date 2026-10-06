#!/usr/bin/env bash
# PreToolUse (Bash): block merge/push to main unless every change passes gate-check
# and the newest change has gate 4 complete.
set -euo pipefail
INPUT="$(cat)"
OUT="$(printf '%s' "$INPUT" | python3 -c '
import json, os, re, subprocess, sys
data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command") or ""
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
risky = False
if re.search(r"\bgh\s+pr\s+merge\b", cmd):
    risky = True
for seg in re.split(r"[;&|\n]+", cmd):
    if re.search(r"\bgit\b.*\bpush\b", seg) and re.search(r"\b(main|master)\b", seg):
        risky = True
    if re.search(r"\bgit\b.*\bmerge\b", seg):
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root,
                                capture_output=True, text=True).stdout.strip()
        if branch in ("main", "master") or re.search(r"\b(main|master)\b", cmd):
            risky = True
print(root)
print("1" if risky else "0")
')"
ROOT="$(printf '%s\n' "$OUT" | sed -n 1p)"
RISKY="$(printf '%s\n' "$OUT" | sed -n 2p)"
[ "$RISKY" = "1" ] || exit 0

CHECK="$ROOT/scripts/gate-check.sh"
if [ ! -x "$CHECK" ]; then
  echo "gate-guard: ไม่พบ scripts/gate-check.sh จึงไม่อนุญาตให้ merge หรือ push เข้า main" >&2
  exit 2
fi
if ! RESULT="$(cd "$ROOT" && "$CHECK" --all 2>&1)"; then
  printf 'gate-guard: ยังไม่อนุญาตให้ merge หรือ push เข้า main เพราะ gate-check ไม่ผ่าน\n%s\n' "$RESULT" >&2
  exit 2
fi
NEWEST="$(ls -d "$ROOT"/docs/changes/[0-9][0-9][0-9]-*/ 2>/dev/null | sort | tail -n 1 || true)"
if [ -z "$NEWEST" ]; then
  echo "gate-guard: ยังไม่มี change ใน docs/changes/ จึงไม่อนุญาตให้ merge หรือ push เข้า main" >&2
  exit 2
fi
if ! RESULT="$(cd "$ROOT" && "$CHECK" "$NEWEST" 4 2>&1)"; then
  printf 'gate-guard: change ล่าสุดยังไม่ผ่าน gate 4\n%s\n' "$RESULT" >&2
  exit 2
fi
exit 0
