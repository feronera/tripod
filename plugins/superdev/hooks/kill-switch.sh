#!/usr/bin/env bash
# PreToolUse (*): stop every tool call while <project>/.pod/kill-switch exists.
# Active only in a project that has pod.yml (the pod kit); elsewhere it allows with a note.
set -euo pipefail
INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd") or ".")')}"
if [ ! -f "$ROOT/pod.yml" ]; then
  echo "ไม่พบ pod kit ใน project นี้ (ไม่มี pod.yml) hook kill-switch จึงไม่ทำงาน" >&2
  exit 0
fi
if [ -e "$ROOT/.pod/kill-switch" ]; then
  echo "kill switch เปิดอยู่ (.pod/kill-switch) agent ต้องหยุดทำงานทุกอย่าง ให้มนุษย์ตรวจสอบแล้วลบไฟล์นี้เอง" >&2
  exit 2
fi
exit 0
