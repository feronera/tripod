#!/usr/bin/env bash
# PreToolUse (*): stop every tool call while <project>/.pod/kill-switch exists.
# Active only in a project that has pod.yml (the pod kit); elsewhere it allows with a note.
set -euo pipefail
INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd") or ".")')}"
if [ ! -f "$ROOT/pod.yml" ]; then
  echo "No pod kit in this project (no pod.yml), so the kill-switch hook is inactive" >&2
  exit 0
fi
if [ -e "$ROOT/.pod/kill-switch" ]; then
  echo "kill switch is on (.pod/kill-switch). The agent must stop all work. A human must investigate and delete this file" >&2
  exit 2
fi
exit 0
