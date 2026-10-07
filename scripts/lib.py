#!/usr/bin/env python3
"""Shared helpers for the pod scripts (Python 3 stdlib only).

Used as a library and as a CLI:
    python3 scripts/lib.py gate <change-dir> <1|2|3|4>
    python3 scripts/lib.py check <change-dir> [upto]
    python3 scripts/lib.py check --all
    python3 scripts/lib.py new-change <slug>
    python3 scripts/lib.py metrics <change-dir>
    python3 scripts/lib.py release-check <change-dir>
    python3 scripts/lib.py mark-revert <change-dir> "<reason>"
    python3 scripts/lib.py test
"""
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGES_DIR = os.path.join(ROOT, "docs", "changes")
TEMPLATES_DIR = os.path.join(ROOT, "docs", "templates")

ARTIFACTS = {1: "intent.md", 2: "spec.md", 3: "plan.md", 4: "acceptance.md"}
# gate -> (owner member, cross member)
OWNERS = {1: ("superbiz", "superdev"), 2: ("superbiz", "superdev"),
          3: ("superdev", "superbiz"), 4: ("superdev", "superbiz")}
LABEL = {"superbiz": "SuperBiz", "superdev": "SuperDev", "escalation": "escalation"}
ESCALATION_GATES = (2, 4)
AUTO_BY = "auto-merge"
INT_KEYS = {"wip_limit": 2, "auto_merge_max_lines": 200, "auto_merge_min_track": 10,
            "acceptance_hours": 48}
# stack keys of pod.yml (defaults keep the Python sample app behavior)
STACK_DEFAULTS = {"test_cmd": "python3 -m unittest discover -s tests -t . -v",
                  "code_dirs": "app", "tests_dir": "tests", "strength": "python",
                  "strength_cmd": ""}
STRENGTH_MODES = ("python", "off", "cmd")
NO_TESTS_EXIT = 5  # unittest (Python 3.12+) and pytest exit 5 when no test ran
CHECKPOINT_ITEMS = ("Blocking first steps", "Independent workstreams",
                    "Shared mutable state", "Smallest safe decomposition")


# ---------- config and parsing ----------

def read_pod_yml(root=ROOT, missing_ok=False):
    """Parse the simple `key: value` pod.yml without PyYAML.
    missing_ok=True returns the defaults when pod.yml does not exist."""
    cfg = {}
    path = os.path.join(root, "pod.yml")
    lines = []
    if not (missing_ok and not os.path.exists(path)):
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        cfg[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("superbiz_email", "superdev_email", "escalation_email",
                "superbiz_github", "superdev_github", "escalation_github"):
        cfg[key] = cfg.get(key, "").lower().lstrip("@")
    for key, default in INT_KEYS.items():
        try:
            cfg[key] = int(cfg.get(key, "") or default)
        except ValueError:
            cfg[key] = default
    cfg["auto_merge"] = cfg.get("auto_merge", "off").lower() or "off"
    for key, default in STACK_DEFAULTS.items():
        cfg[key] = cfg.get(key, "") or default
    cfg["tests_dir"] = cfg["tests_dir"].strip("/") or STACK_DEFAULTS["tests_dir"]
    cfg["strength"] = cfg["strength"].lower()
    return cfg


def code_dirs(cfg):
    """`code_dirs` of pod.yml as a list of relative folders (space or comma separated)."""
    dirs = [d.strip().strip("/") or "." for d in re.split(r"[\s,]+", cfg["code_dirs"]) if d.strip()]
    return dirs or [STACK_DEFAULTS["code_dirs"]]


def run_test_cmd(cfg, root=ROOT, capture=False):
    """Run `test_cmd` from pod.yml. Returns (ok, exit_code, note, output).

    "No tests ran" (exit 5) is accepted only while docs/changes/ has no change yet,
    so a freshly installed project passes, and a project with real work needs tests.
    """
    res = subprocess.run(cfg["test_cmd"], shell=True, cwd=root, text=True,
                         capture_output=capture)
    output = (res.stdout or "") + (res.stderr or "") if capture else ""
    if res.returncode == NO_TESTS_EXIT:
        if change_dirs(root):
            return False, res.returncode, ("pod-test: ไม่มี test ที่รัน (exit 5) แต่ docs/changes/ มี change แล้ว "
                                           "จึงต้องมี test ใน %s/" % cfg["tests_dir"]), output
        return True, res.returncode, ("pod-test: ยังไม่มี test (exit 5) ยอมรับได้เพราะยังไม่มี change "
                                      "ใน docs/changes/"), output
    return res.returncode == 0, res.returncode, "", output


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def blob_hash(path):
    """Same value as `git hash-object <path>`."""
    with open(path, "rb") as fh:
        data = fh.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def read_log(change_dir):
    """Return gates.log entries as a list of dicts, in file order."""
    path = os.path.join(change_dir, "gates.log")
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parts = shlex.split(line)
            except ValueError:
                parts = line.split()
            entry = dict(part.split("=", 1) for part in parts if "=" in part)
            try:
                entry["gate"] = int(entry.get("gate", "0"))
            except ValueError:
                entry["gate"] = 0
            entry["by"] = entry.get("by", "").lower()
            entries.append(entry)
    return entries


def risk_of(change_dir):
    path = os.path.join(change_dir, "intent.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^\s*[-*]?\s*\**Risk\**\s*:\s*\**\s*(low|medium|high)\b", line, re.I)
                if m:
                    return m.group(1).lower()
    return "low"


def read_risk_paths(root=ROOT):
    """Globs from docs/risk-paths (one per line, # comments)."""
    path = os.path.join(root, "docs", "risk-paths")
    globs = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    globs.append(line)
    return globs


def _glob_regex(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out, i = out + "(?:/.*)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def path_matches(path, pattern):
    """gitignore-like match: the path itself or one of its parent folders matches."""
    rx = _glob_regex(pattern.lstrip("/"))
    parts = path.strip("/").split("/")
    return any(rx.match("/".join(parts[:n])) for n in range(len(parts), 0, -1))


def risky_files(files, root=ROOT):
    globs = read_risk_paths(root)
    return [f for f in files if any(path_matches(f, g) for g in globs)]


# ---------- plan.md structure (gate 3) ----------

def md_sections(text):
    """Map of `## heading` -> list of lines under it (### stays inside the section)."""
    sections, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def is_placeholder(value):
    """Empty, `...`, or only template text in angle brackets."""
    kept = []
    for line in value.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if not line or line in ("...", "-") or re.fullmatch(r"<.*>", line):
            continue
        kept.append(line)
    return not kept


def value_problem(value):
    """None when a checkpoint value is filled in, else a Thai reason."""
    v = value.strip().strip("`").strip()
    if is_placeholder(v):
        return "ยังไม่ได้กรอกค่า"
    m = re.match(r"^n/a\b\s*:?\s*(.*)$", v, re.I)
    if m and is_placeholder(m.group(1)):
        return "ใช้ n/a ได้ แต่ต้องมีเหตุผล เช่น `n/a: <เหตุผล>`"
    return None


def check_plan(path):
    """Problems with the plan.md structure the checker relies on (empty = OK)."""
    with open(path, encoding="utf-8") as fh:
        sections = md_sections(fh.read())
    problems = []
    pre = "gate 3: plan.md "
    if "Data shape" not in sections:
        problems.append(pre + "ไม่มีหัวข้อ `## Data shape`")
    elif is_placeholder("\n".join(sections["Data shape"])):
        problems.append(pre + "หัวข้อ `## Data shape` ยังว่างหรือเป็นข้อความตัวอย่าง "
                        "ให้ระบุโครงข้อมูลหลักก่อนเขียน logic")
    if "Throughput checkpoint" not in sections:
        problems.append(pre + "ไม่มีหัวข้อ `## Throughput checkpoint`")
    else:
        lines = sections["Throughput checkpoint"]
        for item in CHECKPOINT_ITEMS:
            found = None
            for line in lines:
                m = re.match(r"^\s*[-*]?\s*%s\s*:(.*)$" % re.escape(item), line, re.I)
                if m:
                    found = m.group(1)
                    break
            if found is None:
                problems.append(pre + "ไม่มีบรรทัด `- %s:` ใน `## Throughput checkpoint`" % item)
            else:
                reason = value_problem(found)
                if reason:
                    problems.append(pre + "`%s` %s" % (item, reason))
    if "Parallel parts" not in sections:
        problems.append(pre + "ไม่มีหัวข้อ `## Parallel parts` "
                        "(ถ้าไม่แบ่งงาน ให้เขียน `none: <เหตุผล>`)")
    else:
        problems.extend(pre + p for p in check_parallel_parts(sections["Parallel parts"]))
    return problems


def check_parallel_parts(lines):
    parts, order, none_reason = {}, [], None
    current = None
    for raw in lines:
        line = raw.strip()
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            order.append(current)
            parts[current] = None
            continue
        bare = line.lstrip("-* ").strip("`").strip()
        if bare.lower().startswith("none:") and current is None:
            none_reason = bare[5:].strip()
        fm = re.match(r"^files\s*:(.*)$", bare, re.I)
        if fm and current is not None:
            parts[current] = [f.strip().strip("`").strip() for f in fm.group(1).split(",")]
            parts[current] = [f for f in parts[current] if f]
    if not order:
        if none_reason is None:
            return ["`## Parallel parts` ต้องมีบรรทัด `none: <เหตุผล>` "
                    "หรืออย่างน้อย 2 ส่วนแบบ `### <ชื่อ>` ที่มีบรรทัด `files:`"]
        if is_placeholder(none_reason):
            return ["`none:` ใน `## Parallel parts` ต้องมีเหตุผล"]
        return []
    problems = []
    if len(order) < 2:
        problems.append("`## Parallel parts` มีเพียง 1 ส่วน (%s) ต้องมีอย่างน้อย 2 ส่วน "
                        "หรือเขียน `none: <เหตุผล>`" % order[0])
    owner = {}
    for name in order:
        files = parts[name]
        if not files or any("<" in f for f in files):
            problems.append("ส่วน `### %s` ไม่มีบรรทัด `files:` ที่ระบุไฟล์จริง" % name)
            continue
        for f in files:
            owner.setdefault(f, []).append(name)
    overlap = sorted(f for f, names in owner.items() if len(set(names)) > 1)
    if overlap:
        problems.append("Parallel parts ใช้ไฟล์ซ้ำกัน: %s (แต่ละส่วนต้องแก้ไฟล์ไม่ทับกัน)"
                        % ", ".join("%s (%s)" % (f, ", ".join(owner[f])) for f in overlap))
    return problems


def git_email(root=ROOT):
    try:
        out = subprocess.run(["git", "config", "user.email"], cwd=root,
                             capture_output=True, text=True, check=False)
        return out.stdout.strip().lower()
    except OSError:
        return ""


def role_for(cfg, gate, email):
    """Return 'owner', 'cross', 'escalation' or None."""
    owner, cross = OWNERS[gate]
    if not email:
        return None
    if cfg["superbiz_email"] == cfg["superdev_email"]:
        return None  # misconfigured pod: one person cannot hold both seats
    if email == cfg[owner + "_email"]:
        return "owner"
    if email == cfg[cross + "_email"]:
        return "cross"
    if email == cfg["escalation_email"]:
        return "escalation"
    return None


def required_roles(gate, risk):
    """Roles for a complete gate (gate 4 here = release-ready: everyone signed)."""
    roles = ["owner", "cross"]
    if risk == "high" and gate in ESCALATION_GATES:
        roles.append("escalation")
    return roles


def merge_roles(risk):
    """Gate 4 merge-ready roles per risk (low may use an auto record instead)."""
    return {"low": ["owner", "cross"], "medium": ["owner"],
            "high": ["owner", "cross", "escalation"]}[risk]


def auto_entry(entries):
    """Latest valid `gate=4 role=auto by=auto-merge` record, or None."""
    found = None
    for e in entries:
        if e["gate"] == 4 and e.get("role") == "auto" and e["by"] == AUTO_BY:
            found = e
    return found


def reverts(entries):
    return [e for e in entries if e.get("event") == "revert"]


def expected_email(cfg, gate, role):
    owner, cross = OWNERS[gate]
    return {"owner": cfg[owner + "_email"], "cross": cfg[cross + "_email"],
            "escalation": cfg["escalation_email"]}[role]


def role_label(gate, role):
    owner, cross = OWNERS[gate]
    return {"owner": "owner (%s)" % LABEL[owner], "cross": "cross (%s)" % LABEL[cross],
            "escalation": "escalation"}[role]


# ---------- checking ----------

def check_gate(change_dir, gate, cfg, entries=None, risk=None, release=False):
    """Return a list of problem strings for one gate (empty = complete).

    Gate 4 is checked as merge-ready by default and as release-ready with release=True.
    """
    entries = read_log(change_dir) if entries is None else entries
    risk = risk_of(change_dir) if risk is None else risk
    problems = []
    if gate == 4 and not release and risk == "low" and auto_entry(entries):
        return problems  # low risk merged by a recorded auto-merge-check ALLOW
    roles = merge_roles(risk) if gate == 4 and not release else required_roles(gate, risk)
    artifact = os.path.join(change_dir, ARTIFACTS[gate])
    current = blob_hash(artifact) if os.path.exists(artifact) else None
    if current is None:
        problems.append("gate %d: ไม่พบ %s / artifact missing" % (gate, ARTIFACTS[gate]))
    elif gate == 3:
        problems.extend(check_plan(artifact))
    indexed = [(i, e) for i, e in enumerate(entries) if e["gate"] == gate]
    latest = {}
    for i, e in indexed:
        latest[e.get("role", "")] = (i, e)
    for role in roles:
        if role not in latest:
            extra = " หรือ auto-merge" if gate == 4 and role == "cross" and risk == "low" \
                and not release else ""
            problems.append("gate %d: ยังไม่มีการอนุมัติจาก %s%s / missing %s approval"
                            % (gate, role_label(gate, role), extra, role))
            continue
        idx, e = latest[role]
        want = expected_email(cfg, gate, role)
        if e["by"] != want:
            problems.append("gate %d: %s ลงชื่อโดย %s ซึ่งไม่ตรงกับ pod.yml (%s) / role mismatch"
                            % (gate, role, e["by"], want or "-"))
        if current is not None and e.get("blob") != current:
            problems.append("gate %d: การอนุมัติของ %s ล้าสมัย เพราะ %s ถูกแก้หลังอนุมัติ / stale approval"
                            % (gate, role, ARTIFACTS[gate]))
        if role != "owner":
            before = [r_e for r_i, r_e in indexed if r_i < idx]
            ok = any(r_e.get("role") == "owner" for r_e in before)
            if gate == 4 and auto_entry(before):
                ok = True  # post-merge acceptance after an auto record
            if not ok:
                problems.append("gate %d: %s ต้องลงชื่อหลัง owner / wrong role order"
                                % (gate, role))
    if "owner" in latest and "cross" in latest:
        if latest["owner"][1]["by"] == latest["cross"][1]["by"]:
            problems.append("gate %d: owner และ cross เป็นคนเดียวกัน (%s) / writer and approver must differ"
                            % (gate, latest["owner"][1]["by"]))
    return problems


def check_change(change_dir, cfg, upto=None):
    entries = read_log(change_dir)
    if upto is None:
        upto = max([e["gate"] for e in entries if 1 <= e["gate"] <= 4], default=0)
    risk = risk_of(change_dir)
    problems = []
    previous_ok = True
    for gate in range(1, upto + 1):
        gate_problems = check_gate(change_dir, gate, cfg, entries, risk)
        if gate > 1 and not previous_ok and any(e["gate"] == gate for e in entries):
            problems.append("gate %d: ต้องผ่าน gate %d ให้ครบก่อน / gate %d requires gate %d complete"
                            % (gate, gate - 1, gate, gate - 1))
        problems.extend(gate_problems)
        previous_ok = previous_ok and not gate_problems
    return problems


def gate_complete(change_dir, gate, cfg):
    """Loose completion test (ignores staleness), used for the WIP count.
    Gate 4 counts as complete once it is merge-ready."""
    entries = read_log(change_dir)
    risk = risk_of(change_dir)
    if gate == 4 and risk == "low" and auto_entry(entries):
        return True
    roles = {e.get("role") for e in entries if e["gate"] == gate}
    need = merge_roles(risk) if gate == 4 else required_roles(gate, risk)
    return all(r in roles for r in need)


def change_dirs(root=ROOT):
    base = os.path.join(root, "docs", "changes")
    if not os.path.isdir(base):
        return []
    return sorted(os.path.join(base, d) for d in os.listdir(base)
                  if re.match(r"^\d{3}-", d) and os.path.isdir(os.path.join(base, d)))


def open_changes(cfg, root=ROOT):
    return [d for d in change_dirs(root)
            if gate_complete(d, 1, cfg) and not gate_complete(d, 4, cfg)]


def rel(path):
    return os.path.relpath(os.path.abspath(path), os.getcwd())


# ---------- commands ----------

def cmd_gate(args):
    if len(args) != 2 or args[1] not in ("1", "2", "3", "4"):
        print("usage: scripts/gate.sh <change-dir> <1|2|3|4>", file=sys.stderr)
        return 2
    change_dir, gate = os.path.abspath(args[0]), int(args[1])
    if not os.path.isdir(change_dir):
        print("ไม่พบโฟลเดอร์ change: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    artifact = os.path.join(change_dir, ARTIFACTS[gate])
    if not os.path.exists(artifact):
        print("ปฏิเสธ: ไม่พบ %s ใน %s ต้องมี artifact ก่อนอนุมัติ gate %d"
              % (ARTIFACTS[gate], args[0], gate), file=sys.stderr)
        return 1
    email = git_email()
    role = role_for(cfg, gate, email)
    if role is None:
        print("ปฏิเสธ: อีเมล git '%s' ไม่มีสิทธิ์ลงชื่อ gate %d ตาม pod.yml "
              "(SuperBiz และ SuperDev ต้องเป็นคนละอีเมล)" % (email or "-", gate), file=sys.stderr)
        return 1
    risk = risk_of(change_dir)
    if role == "escalation" and role not in required_roles(gate, risk):
        print("ปฏิเสธ: gate %d ของ change นี้ (Risk: %s) ไม่ต้องใช้ escalation" % (gate, risk),
              file=sys.stderr)
        return 1
    entries = read_log(change_dir)
    if gate > 1:
        before = check_change(change_dir, cfg, gate - 1)
        if before:
            print("ปฏิเสธ: ต้องผ่าน gate %d ให้ครบก่อน" % (gate - 1), file=sys.stderr)
            for p in before:
                print("  - " + p, file=sys.stderr)
            return 1
    if gate == 3:
        plan_problems = check_plan(artifact)
        if plan_problems:
            print("ปฏิเสธ: plan.md ยังไม่ครบตามรูปแบบ จึงลงชื่อ gate 3 ไม่ได้", file=sys.stderr)
            for p in plan_problems:
                print("  - " + p, file=sys.stderr)
            return 1
    blob = blob_hash(artifact)
    if role != "owner":
        owner_ok = any(e["gate"] == gate and e.get("role") == "owner" and e.get("blob") == blob
                       for e in entries)
        # gate 4: SuperBiz may accept after an auto-merge (post-merge acceptance)
        auto_ok = gate == 4 and role == "cross" and auto_entry(entries) is not None
        if not (owner_ok or auto_ok):
            print("ปฏิเสธ: owner ของ gate %d ต้องอนุมัติ %s ฉบับปัจจุบันก่อน แล้ว %s จึงลงชื่อได้"
                  % (gate, ARTIFACTS[gate], role), file=sys.stderr)
            return 1
    line = "gate=%d role=%s by=%s at=%s blob=%s\n" % (gate, role, email, now_iso(), blob)
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write(line)
    print("บันทึกแล้ว: gate %d role=%s by=%s" % (gate, role, email))
    if gate == 4 and not check_gate(change_dir, 4, cfg):
        print("gate 4 merge-ready แล้ว (Risk: %s)" % risk)
    missing = check_gate(change_dir, gate, cfg, release=True)
    if missing:
        print("gate %d ยังไม่ครบ%s:" % (gate, " สำหรับ release" if gate == 4 else ""))
        for p in missing:
            print("  - " + p)
    else:
        print("gate %d ครบแล้ว" % gate)
    return 0


def cmd_check(args):
    cfg = read_pod_yml()
    if args == ["--all"]:
        dirs, upto = change_dirs(), None
    elif len(args) in (1, 2):
        dirs = [os.path.abspath(args[0])]
        if not os.path.isdir(dirs[0]):
            print("ไม่พบโฟลเดอร์ change: %s" % args[0], file=sys.stderr)
            return 1
        upto = None
        if len(args) == 2:
            if args[1] not in ("1", "2", "3", "4"):
                print("upto ต้องเป็น 1-4", file=sys.stderr)
                return 2
            upto = int(args[1])
    else:
        print("usage: scripts/gate-check.sh <change-dir> [upto] | --all", file=sys.stderr)
        return 2
    failed = False
    if not dirs:
        print("OK: ยังไม่มี change ใน docs/changes/")
    for d in dirs:
        name = os.path.basename(d)
        if upto is None and not os.path.exists(os.path.join(d, "gates.log")):
            print("OK   %s (draft ยังไม่มี gates.log)" % name)
            continue
        problems = check_change(d, cfg, upto)
        if problems:
            failed = True
            print("FAIL %s" % name)
            for p in problems:
                print("  - " + p)
        else:
            entries = read_log(d)
            top = upto or max([e["gate"] for e in entries], default=0)
            note = " merge-ready" if top == 4 else ""
            print("OK   %s (ผ่านถึง gate %d%s, Risk: %s)" % (name, top, note, risk_of(d)))
    return 1 if failed else 0


def cmd_new_change(args):
    if len(args) != 1 or not re.match(r"^[a-z0-9][a-z0-9-]*$", args[0]):
        print("usage: scripts/new-change.sh <slug>   (a-z, 0-9, -)", file=sys.stderr)
        return 2
    cfg = read_pod_yml()
    current = open_changes(cfg)
    if len(current) >= cfg["wip_limit"]:
        print("ปฏิเสธ: งานที่เปิดอยู่ %d ชิ้น ถึง WIP limit (%d) แล้ว ปิดงานให้ผ่าน gate 4 ก่อน:"
              % (len(current), cfg["wip_limit"]), file=sys.stderr)
        for d in current:
            print("  - " + os.path.basename(d), file=sys.stderr)
        return 1
    numbers = [int(os.path.basename(d)[:3]) for d in change_dirs()]
    number = max(numbers, default=0) + 1
    target = os.path.join(CHANGES_DIR, "%03d-%s" % (number, args[0]))
    os.makedirs(target)
    shutil.copy(os.path.join(TEMPLATES_DIR, "intent.md"), os.path.join(target, "intent.md"))
    print(rel(target))
    return 0


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_duration(seconds):
    seconds = int(max(seconds, 0))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    return ("%dd " % days if days else "") + "%dh %02dm" % (hours, minutes)


def cmd_metrics(args):
    if len(args) != 1:
        print("usage: scripts/metrics.sh <change-dir>", file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    intent = os.path.join(change_dir, "intent.md")
    if not os.path.exists(intent):
        print("ไม่พบ intent.md ใน %s" % args[0], file=sys.stderr)
        return 1
    out = subprocess.run(["git", "log", "--follow", "--format=%cI", "--", intent],
                         cwd=change_dir, capture_output=True, text=True, check=False)
    stamps = [s for s in out.stdout.split() if s]
    if not stamps:
        print("intent.md ยังไม่ได้ commit จึงคำนวณเวลาไม่ได้", file=sys.stderr)
        return 1
    start = parse_iso(stamps[-1])
    cfg = read_pod_yml()
    entries = read_log(change_dir)
    risk = risk_of(change_dir)
    print("change: %s   Risk: %s" % (os.path.basename(change_dir), risk))
    print("%-8s %-27s %s" % ("step", "at", "since intent"))
    print("%-8s %-27s %s" % ("intent", start.isoformat(), "0h 00m"))
    finish = None
    for gate in range(1, 5):
        latest = {}
        for e in entries:
            if e["gate"] == gate:
                latest[e.get("role")] = e
        roles = merge_roles(risk) if gate == 4 else required_roles(gate, risk)
        if gate == 4 and risk == "low" and auto_entry(entries):
            latest, roles = {"auto": auto_entry(entries)}, ["auto"]
        if all(r in latest for r in roles):
            done = max(parse_iso(latest[r]["at"]) for r in roles)
            print("%-8s %-27s %s" % ("gate %d" % gate, done.isoformat(),
                                     fmt_duration((done - start).total_seconds())))
            if gate == 4:
                finish = done
        else:
            print("%-8s %-27s %s" % ("gate %d" % gate, "-", "-"))
    if finish is not None:
        print("lead time intent -> gate 4: %s" % fmt_duration((finish - start).total_seconds()))
    else:
        print("lead time intent -> gate 4: ยังไม่ครบ gate 4")
    return 0


def release_problems(change_dir, cfg, now=None):
    """Release-ready: gates 1-4 complete with owner + cross (+ escalation for high),
    all fresh, and no revert. Returns (problems, overdue_message_or_None)."""
    entries = read_log(change_dir)
    risk = risk_of(change_dir)
    problems = check_change(change_dir, cfg, 3)
    problems.extend(check_gate(change_dir, 4, cfg, entries, risk, release=True))
    for e in reverts(entries):
        problems.append("change นี้ถูก revert แล้ว (%s): %s" % (e.get("at", "-"), e.get("reason", "-")))
    overdue = None
    auto = auto_entry(entries)
    has_cross = any(e["gate"] == 4 and e.get("role") == "cross" for e in entries)
    if auto and not has_cross:
        due = parse_iso(auto["at"]).timestamp() + cfg["acceptance_hours"] * 3600
        now = datetime.now(timezone.utc).timestamp() if now is None else now
        if now > due:
            overdue = ("merge อัตโนมัติเมื่อ %s แต่ SuperBiz ยังไม่ตรวจรับเกิน %d ชั่วโมง"
                       % (auto["at"], cfg["acceptance_hours"]))
        else:
            problems.append("merge อัตโนมัติแล้ว รอ SuperBiz ตรวจรับ (gate 4 cross) ภายใน %d ชั่วโมง"
                            % cfg["acceptance_hours"])
    return problems, overdue


def cmd_release_check(args):
    if len(args) != 1:
        print("usage: scripts/release-check.sh <change-dir>", file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    if not os.path.isdir(change_dir):
        print("ไม่พบโฟลเดอร์ change: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    problems, overdue = release_problems(change_dir, cfg)
    name = os.path.basename(change_dir)
    if overdue:
        print("NOT RELEASE-READY %s" % name)
        print("  - " + overdue)
        print("  - ห้ามปล่อยขึ้น production จนกว่า SuperBiz ตรวจรับ")
        for p in problems:
            print("  - " + p)
        return 1
    if problems:
        print("NOT RELEASE-READY %s" % name)
        for p in problems:
            print("  - " + p)
        return 1
    print("RELEASE-READY %s (Risk: %s)" % (name, risk_of(change_dir)))
    return 0


def cmd_mark_revert(args):
    if len(args) != 2 or not args[1].strip():
        print('usage: scripts/mark-revert.sh <change-dir> "<reason>"', file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    if not os.path.isdir(change_dir):
        print("ไม่พบโฟลเดอร์ change: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    email = git_email()
    members = {cfg["superbiz_email"], cfg["superdev_email"], cfg["escalation_email"]} - {""}
    if email not in members:
        print("ปฏิเสธ: อีเมล git '%s' ไม่ใช่สมาชิกใน pod.yml" % (email or "-"), file=sys.stderr)
        return 1
    reason = " ".join(args[1].replace('"', "'").split())
    line = 'event=revert by=%s at=%s reason="%s"\n' % (email, now_iso(), reason)
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write(line)
    print("บันทึก revert แล้ว: %s (release-check จะไม่ผ่าน และนับผลงานต่อเนื่องใหม่)"
          % os.path.basename(change_dir))
    return 0


def cmd_test(args):
    if args:
        print("usage: scripts/pod-test.sh", file=sys.stderr)
        return 2
    cfg = read_pod_yml()
    print("pod-test: %s" % cfg["test_cmd"], flush=True)
    ok, code, note, _ = run_test_cmd(cfg)
    if note:
        print(note)
    if ok:
        return 0
    return code or 1


COMMANDS = {"test": cmd_test, "gate": cmd_gate, "check": cmd_check, "new-change": cmd_new_change,
            "metrics": cmd_metrics, "release-check": cmd_release_check,
            "mark-revert": cmd_mark_revert}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
