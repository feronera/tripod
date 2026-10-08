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
            return False, res.returncode, ("pod-test: no tests ran (exit 5), but docs/changes/ already has a change, "
                                           "so tests are required in %s/" % cfg["tests_dir"]), output
        return True, res.returncode, ("pod-test: no tests yet (exit 5). Accepted because docs/changes/ "
                                      "has no change yet"), output
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
    """None when a checkpoint value is filled in, else the reason."""
    v = value.strip().strip("`").strip()
    if is_placeholder(v):
        return "has no value"
    m = re.match(r"^n/a\b\s*:?\s*(.*)$", v, re.I)
    if m and is_placeholder(m.group(1)):
        return "may be n/a, but needs a reason, e.g. `n/a: <reason>`"
    return None


def check_plan(path):
    """Problems with the plan.md structure the checker relies on (empty = OK)."""
    with open(path, encoding="utf-8") as fh:
        sections = md_sections(fh.read())
    problems = []
    pre = "gate 3: plan.md "
    if "Data shape" not in sections:
        problems.append(pre + "has no `## Data shape` heading")
    elif is_placeholder("\n".join(sections["Data shape"])):
        problems.append(pre + "`## Data shape` is empty or still template text. "
                        "Describe the main data shape before writing logic")
    if "Throughput checkpoint" not in sections:
        problems.append(pre + "has no `## Throughput checkpoint` heading")
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
                problems.append(pre + "has no `- %s:` line in `## Throughput checkpoint`" % item)
            else:
                reason = value_problem(found)
                if reason:
                    problems.append(pre + "`%s` %s" % (item, reason))
    if "Parallel parts" not in sections:
        problems.append(pre + "has no `## Parallel parts` heading "
                        "(if the work is not split, write `none: <reason>`)")
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
            return ["`## Parallel parts` needs a `none: <reason>` line "
                    "or at least 2 `### <name>` parts, each with a `files:` line"]
        if is_placeholder(none_reason):
            return ["`none:` in `## Parallel parts` needs a reason"]
        return []
    problems = []
    if len(order) < 2:
        problems.append("`## Parallel parts` has only 1 part (%s). Add at least 2 parts "
                        "or write `none: <reason>`" % order[0])
    owner = {}
    for name in order:
        files = parts[name]
        if not files or any("<" in f for f in files):
            problems.append("part `### %s` has no `files:` line listing real files" % name)
            continue
        for f in files:
            owner.setdefault(f, []).append(name)
    overlap = sorted(f for f, names in owner.items() if len(set(names)) > 1)
    if overlap:
        problems.append("Parallel parts share files: %s (each part must edit separate files)"
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
        problems.append("gate %d: %s not found (artifact missing)" % (gate, ARTIFACTS[gate]))
    elif gate == 3:
        problems.extend(check_plan(artifact))
    indexed = [(i, e) for i, e in enumerate(entries) if e["gate"] == gate]
    latest = {}
    for i, e in indexed:
        latest[e.get("role", "")] = (i, e)
    for role in roles:
        if role not in latest:
            extra = " or auto-merge" if gate == 4 and role == "cross" and risk == "low" \
                and not release else ""
            problems.append("gate %d: no approval yet from %s%s (missing %s approval)"
                            % (gate, role_label(gate, role), extra, role))
            continue
        idx, e = latest[role]
        want = expected_email(cfg, gate, role)
        if e["by"] != want:
            problems.append("gate %d: %s signed by %s, which does not match pod.yml (%s) (role mismatch)"
                            % (gate, role, e["by"], want or "-"))
        if current is not None and e.get("blob") != current:
            problems.append("gate %d: %s approval is stale because %s changed after approval"
                            % (gate, role, ARTIFACTS[gate]))
        if role != "owner":
            before = [r_e for r_i, r_e in indexed if r_i < idx]
            ok = any(r_e.get("role") == "owner" for r_e in before)
            if gate == 4 and auto_entry(before):
                ok = True  # post-merge acceptance after an auto record
            if not ok:
                problems.append("gate %d: %s must sign after owner (wrong role order)"
                                % (gate, role))
    if "owner" in latest and "cross" in latest:
        if latest["owner"][1]["by"] == latest["cross"][1]["by"]:
            problems.append("gate %d: owner and cross are the same person (%s): writer and approver must differ"
                            % (gate, latest["owner"][1]["by"]))
    return problems


def log_ignored(change_dir):
    """True when git would ignore this change's gates.log (e.g. a global *.log rule).
    Ignored approvals never reach the other person or CI, so the cross-gate silently fails."""
    path = os.path.join(change_dir, "gates.log")
    try:
        res = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return res.returncode == 0


IGNORED_HINT = ("gates.log is ignored by git (often a global *.log rule), so approvals would never be shared. "
                "Add '!docs/changes/*/gates.log' to .gitignore")


def check_change(change_dir, cfg, upto=None):
    if os.path.exists(os.path.join(change_dir, "gates.log")) and log_ignored(change_dir):
        return [IGNORED_HINT]
    entries = read_log(change_dir)
    if upto is None:
        upto = max([e["gate"] for e in entries if 1 <= e["gate"] <= 4], default=0)
    risk = risk_of(change_dir)
    problems = []
    previous_ok = True
    for gate in range(1, upto + 1):
        gate_problems = check_gate(change_dir, gate, cfg, entries, risk)
        if gate > 1 and not previous_ok and any(e["gate"] == gate for e in entries):
            problems.append("gate %d: requires gate %d complete first"
                            % (gate, gate - 1))
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
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    artifact = os.path.join(change_dir, ARTIFACTS[gate])
    if not os.path.exists(artifact):
        print("Refused: %s not found in %s. The artifact must exist before gate %d is approved"
              % (ARTIFACTS[gate], args[0], gate), file=sys.stderr)
        return 1
    email = git_email()
    role = role_for(cfg, gate, email)
    if role is None:
        print("Refused: git email '%s' may not sign gate %d according to pod.yml "
              "(SuperBiz and SuperDev must use different emails)" % (email or "-", gate), file=sys.stderr)
        return 1
    risk = risk_of(change_dir)
    if role == "escalation" and role not in required_roles(gate, risk):
        print("Refused: gate %d of this change (Risk: %s) does not need escalation" % (gate, risk),
              file=sys.stderr)
        return 1
    entries = read_log(change_dir)
    if gate > 1:
        before = check_change(change_dir, cfg, gate - 1)
        if before:
            print("Refused: gate %d must be complete first" % (gate - 1), file=sys.stderr)
            for p in before:
                print("  - " + p, file=sys.stderr)
            return 1
    if gate == 3:
        plan_problems = check_plan(artifact)
        if plan_problems:
            print("Refused: plan.md does not follow the required structure, so gate 3 cannot be signed", file=sys.stderr)
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
            print("Refused: the gate %d owner must approve the current %s before %s can sign"
                  % (gate, ARTIFACTS[gate], role), file=sys.stderr)
            return 1
    if log_ignored(change_dir):
        print("Refused: " + IGNORED_HINT, file=sys.stderr)
        return 1
    line = "gate=%d role=%s by=%s at=%s blob=%s\n" % (gate, role, email, now_iso(), blob)
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write(line)
    print("Recorded: gate %d role=%s by=%s" % (gate, role, email))
    if gate == 4 and not check_gate(change_dir, 4, cfg):
        print("gate 4 is merge-ready (Risk: %s)" % risk)
    missing = check_gate(change_dir, gate, cfg, release=True)
    if missing:
        print("gate %d is not complete%s:" % (gate, " for release" if gate == 4 else ""))
        for p in missing:
            print("  - " + p)
    else:
        print("gate %d is complete" % gate)
    return 0


def cmd_check(args):
    cfg = read_pod_yml()
    if args == ["--all"]:
        dirs, upto = change_dirs(), None
    elif len(args) in (1, 2):
        dirs = [os.path.abspath(args[0])]
        if not os.path.isdir(dirs[0]):
            print("change folder not found: %s" % args[0], file=sys.stderr)
            return 1
        upto = None
        if len(args) == 2:
            if args[1] not in ("1", "2", "3", "4"):
                print("upto must be 1-4", file=sys.stderr)
                return 2
            upto = int(args[1])
    else:
        print("usage: scripts/gate-check.sh <change-dir> [upto] | --all", file=sys.stderr)
        return 2
    failed = False
    if not dirs:
        print("OK: no changes in docs/changes/ yet")
    for d in dirs:
        name = os.path.basename(d)
        if upto is None and not os.path.exists(os.path.join(d, "gates.log")):
            print("OK   %s (draft, no gates.log yet)" % name)
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
            print("OK   %s (passed up to gate %d%s, Risk: %s)" % (name, top, note, risk_of(d)))
    return 1 if failed else 0


def cmd_new_change(args):
    if len(args) != 1 or not re.match(r"^[a-z0-9][a-z0-9-]*$", args[0]):
        print("usage: scripts/new-change.sh <slug>   (a-z, 0-9, -)", file=sys.stderr)
        return 2
    cfg = read_pod_yml()
    current = open_changes(cfg)
    if len(current) >= cfg["wip_limit"]:
        print("Refused: %d open changes reach the WIP limit (%d). Take a change through gate 4 first:"
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
        print("intent.md not found in %s" % args[0], file=sys.stderr)
        return 1
    out = subprocess.run(["git", "log", "--follow", "--format=%cI", "--", intent],
                         cwd=change_dir, capture_output=True, text=True, check=False)
    stamps = [s for s in out.stdout.split() if s]
    if not stamps:
        print("intent.md is not committed yet, so times cannot be computed", file=sys.stderr)
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
        print("lead time intent -> gate 4: gate 4 not complete yet")
    return 0


def release_problems(change_dir, cfg, now=None):
    """Release-ready: gates 1-4 complete with owner + cross (+ escalation for high),
    all fresh, and no revert. Returns (problems, overdue_message_or_None)."""
    entries = read_log(change_dir)
    risk = risk_of(change_dir)
    problems = check_change(change_dir, cfg, 3)
    problems.extend(check_gate(change_dir, 4, cfg, entries, risk, release=True))
    for e in reverts(entries):
        problems.append("this change was reverted (%s): %s" % (e.get("at", "-"), e.get("reason", "-")))
    overdue = None
    auto = auto_entry(entries)
    has_cross = any(e["gate"] == 4 and e.get("role") == "cross" for e in entries)
    if auto and not has_cross:
        due = parse_iso(auto["at"]).timestamp() + cfg["acceptance_hours"] * 3600
        now = datetime.now(timezone.utc).timestamp() if now is None else now
        if now > due:
            overdue = ("auto-merged at %s, but SuperBiz has not accepted it within %d hours"
                       % (auto["at"], cfg["acceptance_hours"]))
        else:
            problems.append("auto-merged, waiting for SuperBiz acceptance (gate 4 cross) within %d hours"
                            % cfg["acceptance_hours"])
    return problems, overdue


def cmd_release_check(args):
    if len(args) != 1:
        print("usage: scripts/release-check.sh <change-dir>", file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    if not os.path.isdir(change_dir):
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    problems, overdue = release_problems(change_dir, cfg)
    name = os.path.basename(change_dir)
    if overdue:
        print("NOT RELEASE-READY %s" % name)
        print("  - " + overdue)
        print("  - Do not release to production until SuperBiz accepts")
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
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    cfg = read_pod_yml()
    email = git_email()
    members = {cfg["superbiz_email"], cfg["superdev_email"], cfg["escalation_email"]} - {""}
    if email not in members:
        print("Refused: git email '%s' is not a member in pod.yml" % (email or "-"), file=sys.stderr)
        return 1
    reason = " ".join(args[1].replace('"', "'").split())
    line = 'event=revert by=%s at=%s reason="%s"\n' % (email, now_iso(), reason)
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write(line)
    print("Revert recorded: %s (release-check will fail, and the track record restarts)"
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
