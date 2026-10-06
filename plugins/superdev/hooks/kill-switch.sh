#!/usr/bin/env bash
# PreToolUse (*): stop every tool call while <project>/.pod/kill-switch exists.
set -euo pipefail
INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd") or ".")')}"
if [ -e "$ROOT/.pod/kill-switch" ]; then
  echo "kill switch เปิดอยู่ (.pod/kill-switch) agent ต้องหยุดทำงานทุกอย่าง ให้มนุษย์ตรวจสอบแล้วลบไฟล์นี้เอง" >&2
  exit 2
fi
exit 0
