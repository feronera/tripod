#!/usr/bin/env python3
"""Install the pod kit core into an existing git repo (Python 3 stdlib only, no network).

usage: scripts/pod-install.sh <target-repo> [--with-sample] [--vendor-plugins] [--force]

- Never overwrites Makefile, AGENTS.md or CLAUDE.md: writes pod.mk, a delimited block in
  AGENTS.md (replaced on re-run), and one `@AGENTS.md` line in CLAUDE.md.
- Other files that already exist are skipped and listed. --force overwrites them and keeps
  the old content as <file>.pod-bak.
- Running it twice changes nothing the second time.
"""
import os
import re
import shutil
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER_FILES = {"pod-install.sh", "pod_install.py"}
DOCS = ["gates.md", "risk-tiers.md", "risk-paths", "merge-by-risk.md", "parallel-agents.md",
        "test-strength.md", "pod-charter.md", "credits.md"]
SAMPLE_TESTS = ["__init__.py", "test_orders.py"]  # the kit's own tests stay in the kit
BEGIN, END = "<!-- pod:begin -->", "<!-- pod:end -->"
GITIGNORE_LINES = [".pod/", "!**/skills/build/"]
STACK_KEYS = ("test_cmd", "code_dirs", "tests_dir", "strength", "strength_cmd")
PY_DEFAULT_CMD = "python3 -m unittest discover -s %s -t . -v"
NOT_CODE = {"tests", "test", "docs", "scripts", "plugins", "build", "dist", "node_modules",
            "venv", "env", "logs", "examples"}


class Installer:
    def __init__(self, target, force=False):
        self.target = target
        self.force = force
        self.created, self.updated, self.unchanged, self.skipped, self.backups = [], [], [], [], []

    # ---------- file helpers ----------

    def path(self, rel):
        return os.path.join(self.target, rel)

    def read(self, rel):
        p = self.path(rel)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as fh:
            return fh.read()

    def write_text(self, rel, text, mode=None, policy="copy"):
        """policy copy: create, or skip/force when different. policy own: always rewrite
        (files the installer manages by blocks: AGENTS.md, CLAUDE.md, .gitignore)."""
        p = self.path(rel)
        current = self.read(rel)
        if current == text:
            self.unchanged.append(rel)
            return
        if current is not None and policy == "copy":
            if not self.force:
                self.skipped.append(rel)
                return
            shutil.copyfile(p, p + ".pod-bak")
            self.backups.append(rel + ".pod-bak")
        os.makedirs(os.path.dirname(p) or self.target, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        if mode is not None:
            os.chmod(p, mode)
        (self.created if current is None else self.updated).append(rel)

    def copy(self, src_rel, dst_rel=None):
        src = os.path.join(KIT, src_rel)
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        mode = os.stat(src).st_mode & 0o777 if os.access(src, os.X_OK) else None
        self.write_text(dst_rel or src_rel, text, mode)

    def copy_tree(self, src_rel, skip=()):
        base = os.path.join(KIT, src_rel)
        for folder, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(files):
                if name in skip or name.endswith(".pyc") or name == ".DS_Store":
                    continue
                rel = os.path.relpath(os.path.join(folder, name), KIT)
                self.copy(rel)


# ---------- stack detection ----------

def detect_stack(target, with_sample):
    """Return (stack name, {stack keys}, [warnings])."""
    def has(name):
        return os.path.exists(os.path.join(target, name))

    py = {"test_cmd": PY_DEFAULT_CMD % "tests", "code_dirs": "app", "tests_dir": "tests",
          "strength": "python", "strength_cmd": ""}
    if with_sample:
        return "python (sample app)", py, []
    if has("package.json"):
        tests = next((d for d in ("tests", "__tests__", "test") if os.path.isdir(os.path.join(target, d))),
                     "tests")
        return "node (package.json)", {"test_cmd": "npm test", "code_dirs": "src", "tests_dir": tests,
                                       "strength": "off", "strength_cmd": ""}, \
            ["ตรวจว่า package.json มี script \"test\" และ code_dirs/tests_dir ใน pod.yml ตรงกับ project"]
    if any(has(n) for n in ("pyproject.toml", "setup.py", "requirements.txt")):
        tests = next((d for d in ("tests", "test") if os.path.isdir(os.path.join(target, d))), "tests")
        pkgs = sorted(d for d in os.listdir(target)
                      if os.path.isdir(os.path.join(target, d)) and not d.startswith(".")
                      and d not in NOT_CODE and d != tests
                      and os.path.isfile(os.path.join(target, d, "__init__.py")))
        code = pkgs[0] if len(pkgs) == 1 else "src"
        warn = [] if len(pkgs) == 1 else ["ระบุ package ไม่ได้ชัดเจน จึงตั้ง code_dirs: src ให้ตรวจ code_dirs ใน pod.yml"]
        warn.append("test_cmd ตั้งเป็น unittest หาก project ใช้ pytest ให้แก้เป็น `python3 -m pytest` "
                    "(strength แบบ python ใช้ได้กับ test แบบ unittest.TestCase เท่านั้น)")
        return "python", {"test_cmd": PY_DEFAULT_CMD % tests, "code_dirs": code, "tests_dir": tests,
                          "strength": "python", "strength_cmd": ""}, warn
    if has("go.mod"):
        return "go (go.mod)", {"test_cmd": "go test ./...", "code_dirs": ".", "tests_dir": "tests",
                               "strength": "off", "strength_cmd": ""}, \
            ["Go เก็บ test ไว้ข้างโค้ด (_test.go) hook protect-tests ล็อกได้เฉพาะ tests_dir ให้ตรวจค่านี้ใน pod.yml"]
    return "unknown", py, ["ไม่พบไฟล์ที่ระบุ stack ได้ (package.json, pyproject.toml, go.mod) "
                           "จึงใช้ค่าเริ่มต้นแบบ Python ให้แก้ test_cmd, code_dirs, tests_dir และ strength ใน pod.yml"]


def pod_yml_text(stack):
    """Kit pod.yml (placeholder people) with the stack keys of this project."""
    with open(os.path.join(KIT, "pod.yml"), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out = []
    for line in lines:
        key, _, rest = line.partition(":")
        if key.strip() in STACK_KEYS and not line.startswith("#"):
            key = key.strip()
            comment = rest[rest.index("#"):] if "#" in rest else ""
            head = "%s: %s" % (key, stack[key]) if stack[key] else "%s:" % key
            if comment:
                head = head.ljust(max(len(head) + 1, 27)) + comment
            out.append(head)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


# ---------- AGENTS.md block ----------

def md_split(text):
    """[(heading or None, text)] split on `## ` headings."""
    parts, current, buf = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            parts.append((current, "\n".join(buf)))
            current, buf = line[3:].strip(), [line]
        else:
            buf.append(line)
    parts.append((current, "\n".join(buf)))
    return parts


def agents_block(stack):
    with open(os.path.join(KIT, "AGENTS.md"), encoding="utf-8") as fh:
        kit = fh.read()
    tests = stack["tests_dir"]
    keep = [body for head, body in md_split(kit)
            if head in ("Pod", "Gates", "กฎที่ห้ามละเมิด", "ที่อยู่ของงาน")]
    text = "\n\n".join(b.strip() for b in keep)
    text = text.replace("`tests/`", "`%s/`" % tests).replace("`make check`", "`make -f pod.mk pod-check`")
    stack_md = "\n".join([
        "## Stack และคำสั่งของ pod",
        "- คำสั่ง test, โฟลเดอร์โค้ด, โฟลเดอร์ test และวิธีตรวจ test-strength อยู่ใน `pod.yml`"
        " (`test_cmd`, `code_dirs`, `tests_dir`, `strength`)",
        "- ใน skill ของ plugin คำว่า `make test` หมายถึง `make -f pod.mk pod-test`"
        " และ `make check` หมายถึง `make -f pod.mk pod-check` (หรือ target ที่ Makefile ของ project ตั้งชื่อไว้)",
        "- `app/` และ `tests/` ใน skill หมายถึง `code_dirs` และ `tests_dir` ใน pod.yml",
        "- `make -f pod.mk pod-test`: รัน `test_cmd`",
        "- `make -f pod.mk pod-strength`: `scripts/test-strength.sh` ตามโหมด `strength` (ดู `docs/test-strength.md`)",
        "- `make -f pod.mk pod-check`: test, strength, ตรวจ CODEOWNERS และ `scripts/gate-check.sh --all` (CI ใช้คำสั่งนี้)",
        "- `scripts/auto-merge-check.sh <dir> [--base main] [--record]`: ALLOW หรือ DENY สำหรับ merge อัตโนมัติ",
        "- `scripts/release-check.sh <dir>`: พร้อมปล่อยขึ้น production หรือไม่",
        "- `make -f pod.mk pod-metrics CHANGE=docs/changes/NNN-slug`: เวลาจาก intent ถึงแต่ละ gate",
    ])
    return "%s\n# Pod (ADLC SuperBiz x SuperDev)\n\nส่วนนี้สร้างโดย scripts/pod-install.sh ของ pod kit " \
           "การรันติดตั้งซ้ำจะแทนที่ส่วนนี้ทั้งหมด ให้เพิ่มกฎของทีมไว้นอกส่วนนี้\n\n%s\n\n%s\n%s\n" \
           % (BEGIN, text, stack_md, END)


def with_block(current, block):
    if current is None:
        return "# AGENTS.md\n\nกฎสำหรับ agent ทุกตัวใน repo นี้ (Claude Code อ่านผ่าน CLAUDE.md)\n\n" + block
    if BEGIN in current and END in current:
        head, rest = current.split(BEGIN, 1)
        tail = rest.split(END, 1)[1]
        return head + block.rstrip("\n") + tail
    sep = "" if current.endswith("\n\n") else ("\n" if current.endswith("\n") else "\n\n")
    return current + sep + block


# ---------- Makefile and pod.mk ----------

ALIAS_MAKEFILE = """include pod.mk

.PHONY: setup test strength check metrics

setup: pod-setup
test: pod-test
strength: pod-strength
check: pod-check
metrics: pod-metrics
"""


def makefile_includes_pod(text):
    return re.search(r"^\s*-?include\s+.*\bpod\.mk\b", text or "", re.M) is not None


# ---------- main ----------

def parse_args(argv):
    opts = {"with_sample": False, "vendor_plugins": False, "force": False}
    target = None
    for a in argv:
        if a in ("--with-sample", "--vendor-plugins", "--force"):
            opts[a[2:].replace("-", "_")] = True
        elif a.startswith("-") or target is not None:
            return None, opts
        else:
            target = a
    return target, opts


def main(argv):
    target, opts = parse_args(argv)
    if target is None:
        print("usage: scripts/pod-install.sh <target-repo> [--with-sample] [--vendor-plugins] [--force]",
              file=sys.stderr)
        return 2
    target = os.path.realpath(target)
    if not os.path.isdir(target):
        print("ไม่พบโฟลเดอร์ %s" % target, file=sys.stderr)
        return 1
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=target,
                         capture_output=True, text=True)
    if res.returncode != 0:
        print("ปฏิเสธ: %s ไม่ใช่ git repo (รัน git init ก่อน)" % target, file=sys.stderr)
        return 1
    if os.path.realpath(res.stdout.strip()) != target:
        print("ปฏิเสธ: ต้องระบุโฟลเดอร์บนสุดของ git repo (%s)" % res.stdout.strip(), file=sys.stderr)
        return 1
    if os.path.realpath(KIT) == target:
        print("ปฏิเสธ: target คือ pod kit เอง", file=sys.stderr)
        return 1

    stack_name, stack, warnings = detect_stack(target, opts["with_sample"])
    inst = Installer(target, force=opts["force"])

    # kit core
    for name in sorted(os.listdir(os.path.join(KIT, "scripts"))):
        src = os.path.join(KIT, "scripts", name)
        if os.path.isfile(src) and name not in INSTALLER_FILES and name.endswith((".sh", ".py")):
            inst.copy(os.path.join("scripts", name))
    for name in DOCS:
        inst.copy(os.path.join("docs", name))
    inst.copy_tree(os.path.join("docs", "templates"))
    inst.copy(os.path.join("docs", "changes", ".gitkeep"))
    inst.copy(os.path.join(".github", "workflows", "pod-gates.yml"))
    inst.write_text("pod.yml", pod_yml_text(stack))
    inst.copy("pod.mk")
    if opts["vendor_plugins"]:
        inst.copy_tree("plugins")
    if opts["with_sample"]:
        inst.copy_tree("app")
        for name in SAMPLE_TESTS:
            inst.copy(os.path.join("tests", name))
        inst.copy_tree("logs")
    elif stack["strength"] == "python" and not os.path.exists(inst.path(stack["tests_dir"])):
        # unittest needs an importable start dir; an empty package gives "no tests ran" (exit 5)
        inst.write_text(os.path.join(stack["tests_dir"], "__init__.py"), "")

    # Makefile: never overwritten
    makefile = inst.read("Makefile")
    include_hint = None
    if makefile is None:
        inst.write_text("Makefile", ALIAS_MAKEFILE)
    elif makefile == ALIAS_MAKEFILE:
        inst.unchanged.append("Makefile")
    elif not makefile_includes_pod(makefile):
        include_hint = "include pod.mk"

    # AGENTS.md block (replaced on re-run) and CLAUDE.md -> @AGENTS.md
    inst.write_text("AGENTS.md", with_block(inst.read("AGENTS.md"), agents_block(stack)), policy="own")
    claude = inst.read("CLAUDE.md")
    if claude is None:
        inst.write_text("CLAUDE.md", "@AGENTS.md\n", policy="own")
    elif not re.search(r"^@AGENTS\.md\s*$", claude, re.M):
        sep = "" if claude.endswith("\n") or not claude else "\n"
        inst.write_text("CLAUDE.md", claude + sep + "\n@AGENTS.md\n", policy="own")
    else:
        inst.unchanged.append("CLAUDE.md")

    # .gitignore lines, once
    gi = inst.read(".gitignore")
    have = set((gi or "").splitlines())
    missing = [line for line in GITIGNORE_LINES if line not in have]
    if missing:
        sep = "" if not gi or gi.endswith("\n") else "\n"
        inst.write_text(".gitignore", (gi or "") + sep + "# pod kit\n" + "\n".join(missing) + "\n",
                        policy="own")
    else:
        inst.unchanged.append(".gitignore")

    report(inst, target, stack_name, stack, warnings, include_hint, opts)
    return 0


def report(inst, target, stack_name, stack, warnings, include_hint, opts):
    print("pod-install: %s" % target)
    print("stack: %s (test_cmd: %s, code_dirs: %s, tests_dir: %s, strength: %s)"
          % (stack_name, stack["test_cmd"], stack["code_dirs"], stack["tests_dir"], stack["strength"]))
    for label, items in (("สร้างใหม่", inst.created), ("แก้ไข", inst.updated),
                         ("สำรองไฟล์เดิม", inst.backups)):
        if items:
            print("%s %d ไฟล์:" % (label, len(items)))
            for rel in items:
                print("  + " + rel)
    if inst.skipped:
        print("ข้าม %d ไฟล์ที่มีอยู่แล้วและเนื้อหาต่างจาก kit (ใช้ --force เพื่อเขียนทับ โดยสำรองเป็น .pod-bak):"
              % len(inst.skipped))
        for rel in inst.skipped:
            print("  - " + rel)
    print("ไม่เปลี่ยน %d ไฟล์ (เนื้อหาตรงกับ kit แล้ว)" % len(inst.unchanged))
    if not (inst.created or inst.updated):
        print("ไม่มีการเปลี่ยนแปลง")
    if include_hint:
        print("Makefile ของ project มีอยู่แล้วและไม่ได้แก้ ให้เพิ่มบรรทัดนี้ใน Makefile หากต้องการเรียกผ่าน make:")
        print("  " + include_hint)
    for w in warnings:
        print("คำเตือน: " + w)
    print("")
    print("ขั้นตอนต่อไป")
    steps = [
        "แก้ pod.yml: ชื่อ อีเมล (ตรงกับ git config user.email) และบัญชี GitHub ของ SuperBiz, SuperDev และ escalation"
        " แล้วตรวจ test_cmd, code_dirs, tests_dir และ strength",
        "แก้ docs/risk-paths ให้ตรงกับ path อ่อนไหวของ project นี้",
        "รัน scripts/sync-codeowners.sh เพื่อสร้าง .github/CODEOWNERS",
        "รัน make -f pod.mk pod-setup แล้ว make -f pod.mk pod-check ต้องผ่าน",
        "ติดตั้ง plugin ต่อคน: /plugin marketplace add hx-natthawat/workshop-ai-sdlc แล้ว"
        " /plugin install superbiz@adlc-pod หรือ superdev@adlc-pod",
        "รัน scripts/setup-github.sh <owner/repo> เพื่อดูแผนก่อน แล้วรันซ้ำพร้อม --yes",
        "commit ไฟล์ทั้งหมดผ่าน PR และอ่าน docs/adopt.md ของ kit สำหรับ change แรกแบบนำร่อง",
    ]
    if opts["vendor_plugins"]:
        steps[4] = ("plugin ถูกคัดลอกไว้ใน plugins/ แล้ว โหลดด้วย claude --plugin-dir ./plugins/superbiz"
                    " หรือ ./plugins/superdev")
    for i, step in enumerate(steps, 1):
        print("%d. %s" % (i, step))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
