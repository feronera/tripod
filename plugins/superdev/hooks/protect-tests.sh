#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): when .pod/lock-tests exists, files under tests_dir
# (pod.yml, default tests) are read-only. Active only in a project that has pod.yml.
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
tests_dir = "tests"
pod_yml = os.path.join(root, "pod.yml")
if os.path.isfile(pod_yml):
    with open(pod_yml, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line.startswith("tests_dir:"):
                tests_dir = line.split(":", 1)[1].strip().strip("\"").strip("\x27").strip("/") or "tests"
print(root)
print(rel)
print(tests_dir)
')"
ROOT="$(printf '%s\n' "$OUT" | sed -n 1p)"
REL="$(printf '%s\n' "$OUT" | sed -n 2p)"
TESTS_DIR="$(printf '%s\n' "$OUT" | sed -n 3p)"
if [ ! -f "$ROOT/pod.yml" ]; then
  echo "ไม่พบ pod kit ใน project นี้ (ไม่มี pod.yml) hook protect-tests จึงไม่ทำงาน" >&2
  exit 0
fi
if [ -e "$ROOT/.pod/lock-tests" ]; then
  case "$REL" in
    "$TESTS_DIR"/*)
      echo "tests ถูกล็อกแล้ว (.pod/lock-tests) ห้ามแก้ $REL ให้แก้โค้ดจนกว่า test ทั้งหมดจะผ่าน หากเห็นว่า test ผิด ให้หยุดและแจ้ง SuperDev" >&2
      exit 2 ;;
  esac
fi
exit 0
