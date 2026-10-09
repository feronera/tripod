#!/usr/bin/env bash
# PostToolUse (*), Stop, SubagentStop, SessionEnd: record agent activity and cost for the active change
# (docs/activity-log.md). The logic lives in the project's scripts/activity.py, so the project's kit
# version decides the format. Never blocks the agent: always exits 0.
INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd") or ".")
except Exception: print(".")' 2>/dev/null)}"
if [ -f "$ROOT/pod.yml" ] && [ -f "$ROOT/scripts/activity.py" ]; then
  printf '%s' "$INPUT" | python3 "$ROOT/scripts/activity.py" hook --root "$ROOT" || true
fi
exit 0
