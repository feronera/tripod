#!/usr/bin/env python3
"""Shared helpers for the pod scripts (Python 3 stdlib only).

Used as a library and as a CLI:
    python3 scripts/lib.py gate <change-dir> <1|2|3|4>
    python3 scripts/lib.py check <change-dir> [upto]
    python3 scripts/lib.py check --all
    python3 scripts/lib.py new-change <slug>
    python3 scripts/lib.py metrics <change-dir>
"""
import hashlib
import os
import re
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


# ---------- config and parsing ----------

def read_pod_yml(root=ROOT):
    """Parse the simple `key: value` pod.yml without PyYAML."""
    cfg = {}
    path = os.path.join(root, "pod.yml")
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            cfg[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("superbiz_email", "superdev_email", "escalation_email"):
        cfg[key] = cfg.get(key, "").lower()
    try:
        cfg["wip_limit"] = int(cfg.get("wip_limit", "2") or 2)
    except ValueError:
        cfg["wip_limit"] = 2
    return cfg


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
            entry = dict(part.split("=", 1) for part in line.split() if "=" in part)
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
    roles = ["owner", "cross"]
    if risk == "high" and gate in ESCALATION_GATES:
        roles.append("escalation")
    return roles


def expected_email(cfg, gate, role):
    owner, cross = OWNERS[gate]
    return {"owner": cfg[owner + "_email"], "cross": cfg[cross + "_email"],
            "escalation": cfg["escalation_email"]}[role]


def role_label(gate, role):
    owner, cross = OWNERS[gate]
    return {"owner": "owner (%s)" % LABEL[owner], "cross": "cross (%s)" % LABEL[cross],
            "escalation": "escalation"}[role]


# ---------- checking ----------

def check_gate(change_dir, gate, cfg, entries=None, risk=None):
    """Return a list of problem strings for one gate (empty = complete)."""
    entries = read_log(change_dir) if entries is None else entries
    risk = risk_of(change_dir) if risk is None else risk
    problems = []
    artifact = os.path.join(change_dir, ARTIFACTS[gate])
    current = blob_hash(artifact) if os.path.exists(artifact) else None
    if current is None:
        problems.append("gate %d: ไม่พบ %s / artifact missing" % (gate, ARTIFACTS[gate]))
    indexed = [(i, e) for i, e in enumerate(entries) if e["gate"] == gate]
    latest = {}
    for i, e in indexed:
        latest[e.get("role", "")] = (i, e)
    for role in required_roles(gate, risk):
        if role not in latest:
            problems.append("gate %d: ยังไม่มีการอนุมัติจาก %s / missing %s approval"
                            % (gate, role_label(gate, role), role))
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
            if not any(r_i < idx for r_i, r_e in indexed if r_e.get("role") == "owner"):
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
    """Loose completion test (ignores staleness), used for the WIP count."""
    entries = read_log(change_dir)
    risk = risk_of(change_dir)
    roles = {e.get("role") for e in entries if e["gate"] == gate}
    return all(r in roles for r in required_roles(gate, risk))


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
    blob = blob_hash(artifact)
    if role != "owner":
        if not any(e["gate"] == gate and e.get("role") == "owner" and e.get("blob") == blob
                   for e in entries):
            print("ปฏิเสธ: owner ของ gate %d ต้องอนุมัติ %s ฉบับปัจจุบันก่อน แล้ว %s จึงลงชื่อได้"
                  % (gate, ARTIFACTS[gate], role), file=sys.stderr)
            return 1
    at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    line = "gate=%d role=%s by=%s at=%s blob=%s\n" % (gate, role, email, at, blob)
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write(line)
    print("บันทึกแล้ว: gate %d role=%s by=%s" % (gate, role, email))
    missing = check_gate(change_dir, gate, cfg)
    if missing:
        print("gate %d ยังไม่ครบ:" % gate)
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
            print("OK   %s (ผ่านถึง gate %d, Risk: %s)" % (name, top, risk_of(d)))
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
        roles = required_roles(gate, risk)
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


COMMANDS = {"gate": cmd_gate, "check": cmd_check, "new-change": cmd_new_change,
            "metrics": cmd_metrics}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
