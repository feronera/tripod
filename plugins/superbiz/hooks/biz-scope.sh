#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): SuperBiz may edit only files under docs/.
# In a project without pod.yml or scripts/gate-check.sh (no pod kit) it allows with a note.
set -euo pipefail
INPUT="$(cat)"
# Prints the project dir, then the target path relative to it.
OUT="$(printf '%s' "$INPUT" | python3 -c '
import json, os, sys
data = json.load(sys.stdin)
ti = data.get("tool_input") or {}
target = ti.get("file_path") or ti.get("notebook_path") or ""
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
root = os.path.realpath(root)
print(root)
if not target:
    print("")
    sys.exit(0)
if not os.path.isabs(target):
    target = os.path.join(data.get("cwd") or root, target)
target = os.path.normpath(target)
parent = os.path.realpath(os.path.dirname(target))
print(os.path.relpath(os.path.join(parent, os.path.basename(target)), root))
')"
ROOT="$(printf '%s\n' "$OUT" | sed -n 1p)"
REL="$(printf '%s\n' "$OUT" | sed -n 2p)"
if [ ! -f "$ROOT/pod.yml" ] || [ ! -f "$ROOT/scripts/gate-check.sh" ]; then
  echo "No pod kit in this project (no pod.yml or scripts/gate-check.sh), so the biz-scope hook is inactive" >&2
  exit 0
fi
case "$REL" in
  docs/*) exit 0 ;;
esac
echo "SuperBiz may edit only docs/ (requested file: ${REL:-not given}). Hand code, test or config work to SuperDev" >&2
exit 2
