#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): SuperBiz may edit only files under docs/.
set -euo pipefail
INPUT="$(cat)"
# Prints "<project-dir>\t<path relative to project>" for the target file.
REL="$(printf '%s' "$INPUT" | python3 -c '
import json, os, sys
data = json.load(sys.stdin)
ti = data.get("tool_input") or {}
target = ti.get("file_path") or ti.get("notebook_path") or ""
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
root = os.path.realpath(root)
if not target:
    print("")
    sys.exit(0)
if not os.path.isabs(target):
    target = os.path.join(data.get("cwd") or root, target)
target = os.path.normpath(target)
parent = os.path.realpath(os.path.dirname(target))
print(os.path.relpath(os.path.join(parent, os.path.basename(target)), root))
')"
case "$REL" in
  docs/*) exit 0 ;;
esac
echo "SuperBiz แก้ได้เฉพาะ docs/ (ไฟล์ที่ขอแก้: ${REL:-ไม่ระบุ}) งานโค้ด test หรือ config ให้ส่งต่อให้ SuperDev" >&2
exit 2
