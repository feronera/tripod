#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): when .pod/lock-tests exists, files under tests/ are read-only.
set -euo pipefail
INPUT="$(cat)"
OUT="$(printf '%s' "$INPUT" | python3 -c '
import json, os, sys
data = json.load(sys.stdin)
ti = data.get("tool_input") or {}
target = ti.get("file_path") or ti.get("notebook_path") or ""
root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
rel = ""
if target:
    if not os.path.isabs(target):
        target = os.path.join(data.get("cwd") or root, target)
    target = os.path.normpath(target)
    parent = os.path.realpath(os.path.dirname(target))
    rel = os.path.relpath(os.path.join(parent, os.path.basename(target)), root)
print(root)
print(rel)
')"
ROOT="$(printf '%s\n' "$OUT" | sed -n 1p)"
REL="$(printf '%s\n' "$OUT" | sed -n 2p)"
if [ -e "$ROOT/.pod/lock-tests" ]; then
  case "$REL" in
    tests/*)
      echo "tests ถูกล็อกแล้ว (.pod/lock-tests) ห้ามแก้ $REL ให้แก้โค้ดใน app/ จนกว่า make test จะผ่าน หากเห็นว่า test ผิด ให้หยุดและแจ้ง SuperDev" >&2
      exit 2 ;;
  esac
fi
exit 0
