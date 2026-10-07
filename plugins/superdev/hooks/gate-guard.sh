#!/usr/bin/env bash
# PreToolUse (Bash): block merge/push to main unless every change passes gate-check
# and the newest change is merge-ready at gate 4 (per risk, see docs/merge-by-risk.md):
#   low: owner + cross, or a `role=auto` record from scripts/auto-merge-check.sh --record
#   medium: owner (SuperDev)   high: owner + cross + escalation
# In a project without pod.yml or scripts/gate-check.sh (no pod kit) it allows with a note.
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
CHECK="$ROOT/scripts/gate-check.sh"
if [ ! -f "$ROOT/pod.yml" ] || [ ! -f "$CHECK" ]; then
  echo "No pod kit in this project (no pod.yml or scripts/gate-check.sh), so the gate-guard hook is inactive" >&2
  exit 0
fi
[ "$RISKY" = "1" ] || exit 0
if [ ! -x "$CHECK" ]; then
  echo "gate-guard: scripts/gate-check.sh is not executable. Run make setup (or make -f pod.mk pod-setup) first" >&2
  exit 2
fi
if ! RESULT="$(cd "$ROOT" && "$CHECK" --all 2>&1)"; then
  printf 'gate-guard: merge or push to main is not allowed yet because gate-check failed\n%s\n' "$RESULT" >&2
  exit 2
fi
NEWEST="$(ls -d "$ROOT"/docs/changes/[0-9][0-9][0-9]-*/ 2>/dev/null | sort | tail -n 1 || true)"
if [ -z "$NEWEST" ]; then
  echo "gate-guard: docs/changes/ has no change yet, so merge or push to main is not allowed" >&2
  exit 2
fi
if ! RESULT="$(cd "$ROOT" && "$CHECK" "$NEWEST" 4 2>&1)"; then
  printf 'gate-guard: the newest change is not merge-ready at gate 4 (see docs/merge-by-risk.md)\n%s\n' "$RESULT" >&2
  exit 2
fi
exit 0
