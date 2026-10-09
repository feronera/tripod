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
    # Role keys may hold comma-separated lists, aligned by position (see members()).
    for key in ("superbiz_email", "superdev_email", "escalation_email",
                "superbiz_github", "superdev_github", "escalation_github"):
        cfg[key] = ", ".join(v.lower().lstrip("@") for v in split_list(cfg.get(key, "")))
    for key in ("superbiz_name", "superdev_name", "escalation_name"):
        cfg[key] = ", ".join(split_list(cfg.get(key, "")))
    cfg["base_branch"] = cfg.get("base_branch", "") or "main"
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


def split_list(value):
    """Comma-separated pod.yml value as a list of non-empty, stripped items."""
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def members(cfg, role):
    """People in a role ("superbiz", "superdev" or "escalation") as a list of
    {name, email, github}. The name, email and github lists are aligned by position;
    a missing position is an empty string (pod_config_problems reports the mismatch)."""
    lists = {f: split_list(cfg.get("%s_%s" % (role, f), "")) for f in ("name", "email", "github")}
    count = max(len(v) for v in lists.values())
    return [{f: (lists[f][i] if i < len(lists[f]) else "") for f in lists} for i in range(count)]


def role_emails(cfg, role):
    return [m["email"] for m in members(cfg, role) if m["email"]]


def role_logins(cfg, role):
    return [m["github"] for m in members(cfg, role) if m["github"]]


def roles_of_email(cfg, email):
    """Every role whose email list contains `email` (case-insensitive)."""
    email = (email or "").lower()
    return [r for r in ("superbiz", "superdev", "escalation") if email and email in role_emails(cfg, r)]


SCALING_WARNING = ("SuperBiz owns or cross-checks every gate; with more than 3 SuperDevs per SuperBiz, "
                   "changes will queue at SuperBiz. Add a SuperBiz or split into two pods (docs/scaling.md).")


def pod_config_problems(cfg):
    """(errors, warnings) for the people in pod.yml."""
    errors, warnings = [], []
    for field in ("email", "github"):
        seen = {}
        for role in ("superbiz", "superdev", "escalation"):
            for value in {m[field] for m in members(cfg, role) if m[field]}:
                seen.setdefault(value, []).append(LABEL[role])
        for value, roles in sorted(seen.items()):
            if len(roles) > 1:
                errors.append("pod.yml: %s %s appears in more than one role (%s). One person holds one role"
                              % ("email" if field == "email" else "GitHub login", value, ", ".join(roles)))
    for role in ("superbiz", "superdev", "escalation"):
        counts = {f: len(split_list(cfg.get("%s_%s" % (role, f), ""))) for f in ("name", "email", "github")}
        size = max(counts.values())
        if size > 1:
            bad = [f for f, n in counts.items() if n != size and not (f == "github" and n == 0)]
            if bad:
                errors.append("pod.yml: the %s lists have different lengths (%s). Give one value per person, "
                              "in the same order" % (LABEL[role], ", ".join(
                                  "%s_%s: %d" % (role, f, n) for f, n in counts.items())))
    bizs, devs = len(role_emails(cfg, "superbiz")), len(role_emails(cfg, "superdev"))
    if bizs and devs > 3 * bizs:
        warnings.append(SCALING_WARNING)
    return errors, warnings


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


def check_plan(path, cfg=None):
    """Problems with the plan.md structure the checker relies on (empty = OK).
    With cfg, a part's `owner:` must be a SuperDev in pod.yml."""
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
        problems.extend(pre + p for p in check_parallel_parts(sections["Parallel parts"], cfg))
    return problems


def check_parallel_parts(lines, cfg=None):
    parts, tests, owners, order, none_reason = {}, {}, {}, [], None
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
        tm = re.match(r"^tests\s*:(.*)$", bare, re.I)
        if tm and current is not None:
            tests[current] = [f.strip().strip("`").strip() for f in tm.group(1).split(",")]
            tests[current] = [f for f in tests[current] if f]
        om = re.match(r"^owner\s*:(.*)$", bare, re.I)
        if om and current is not None:
            owners[current] = om.group(1).strip().strip("`").strip().lower()
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
    # Each part needs its own tests, so it can go green without waiting for another part.
    test_owner = {}
    for name in order:
        files = tests.get(name)
        if not files or any("<" in f for f in files):
            problems.append("part `### %s` has no `tests:` line listing its own test files "
                            "(each part must be testable on its own)" % name)
            continue
        for f in files:
            test_owner.setdefault(f, []).append(name)
            if f in owner and name not in owner[f]:
                problems.append("part `### %s` lists %s under tests:, but part %s edits it"
                                % (name, f, ", ".join(owner[f])))
    shared = sorted(f for f, names in test_owner.items() if len(set(names)) > 1)
    if shared:
        problems.append("Parallel parts share test files: %s (give each part its own test files)"
                        % ", ".join("%s (%s)" % (f, ", ".join(test_owner[f])) for f in shared))
    if cfg is not None:
        devs = role_emails(cfg, "superdev")
        for name in order:
            who = owners.get(name)
            if who is not None and who not in devs:
                problems.append("part `### %s` has owner: %s, who is not a SuperDev in pod.yml (superdev_email: %s)"
                                % (name, who or "-", ", ".join(devs) or "-"))
    return problems


def parallel_parts(plan_path):
    """{part: (files, tests)} from plan.md, or {} when the work is not split."""
    with open(plan_path, encoding="utf-8") as fh:
        lines = md_sections(fh.read()).get("Parallel parts", [])
    result, current = {}, None
    for raw in lines:
        line = raw.strip()
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            result[current] = ([], [])
            continue
        bare = line.lstrip("-* ").strip("`").strip()
        for i, key in enumerate(("files", "tests")):
            km = re.match(r"^%s\s*:(.*)$" % key, bare, re.I)
            if km and current is not None:
                result[current][i].extend(f.strip().strip("`").strip()
                                          for f in km.group(1).split(",") if f.strip())
    return result


def part_owners(plan_path):
    """{part: owner email} for parts of plan.md that have an `owner:` line."""
    with open(plan_path, encoding="utf-8") as fh:
        lines = md_sections(fh.read()).get("Parallel parts", [])
    owners, current = {}, None
    for raw in lines:
        line = raw.strip()
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            continue
        bare = line.lstrip("-* ").strip("`").strip()
        om = re.match(r"^owner\s*:(.*)$", bare, re.I)
        if om and current is not None and om.group(1).strip():
            owners[current] = om.group(1).strip().strip("`").strip().lower()
    return owners


def part_label(name, owners):
    return "%s (owner: %s)" % (name, owners[name]) if name in owners else name


def python_imports(path):
    """Dotted module names a Python file imports, including `from pkg import name` as pkg.name."""
    import ast
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names.update("%s.%s" % (node.module, a.name) for a in node.names)
    return names


def git_out(args, cwd):
    res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=False)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def run_parallel_isolated(change_dir, parts, base, owners=None):
    """After the build: run each part's tests in a throwaway worktree where every other part's files
    are put back to how they are at `base`. A part that fails there depends on another part."""
    import tempfile
    owners = owners or {}
    rc, merge_base, err = git_out(["merge-base", "HEAD", base], ROOT)
    if rc != 0:
        print("cannot find the merge base of HEAD and %s: %s" % (base, err), file=sys.stderr)
        return 2
    results, notes = {}, []
    for name, (_, tests) in parts.items():
        py = [t for t in tests if t.endswith(".py")]
        notes.extend("%s: %s is not Python, so it was not run" % (name, t) for t in tests if not t.endswith(".py"))
        if not py:
            continue
        tmp = tempfile.mkdtemp(prefix="pod-parallel-")
        wt = os.path.join(tmp, "wt")
        rc, _, err = git_out(["worktree", "add", "--detach", "-q", wt, "HEAD"], ROOT)
        if rc != 0:
            print("cannot create a worktree: %s" % err, file=sys.stderr)
            return 2
        try:
            for other, (files, _) in parts.items():
                if other == name:
                    continue
                for f in files:
                    in_base = git_out(["cat-file", "-e", "%s:%s" % (merge_base, f)], wt)[0] == 0
                    if in_base:
                        git_out(["checkout", merge_base, "--", f], wt)
                    elif os.path.exists(os.path.join(wt, f)):
                        os.remove(os.path.join(wt, f))
            modules = [t[:-3].replace("/", ".") for t in py]
            res = subprocess.run([sys.executable, "-m", "unittest"] + modules, cwd=wt,
                                 capture_output=True, text=True, check=False)
            summary = [l for l in res.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
            results[name] = (res.returncode == 0, " ".join(summary[-2:]))
        finally:
            git_out(["worktree", "remove", "--force", wt], ROOT)
            shutil.rmtree(tmp, ignore_errors=True)
    for n in notes:
        print("note: " + n)
    failed = [n for n, (ok, _) in results.items() if not ok]
    for name, (ok, summary) in results.items():
        print("%s %s: tests without the other parts' code: %s"
              % ("PASS" if ok else "FAIL", part_label(name, owners), summary))
    if failed:
        print("The parts were not independent: %s needs code from another part. Merge the part it needs first, "
              "and next time build that interface first as a Blocking first step." % ", ".join(failed))
        return 1
    print("OK: every part's tests pass without the other parts' code")
    return 0


def cmd_parallel_check(args):
    run, base = False, "main"
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--run":
            run = True
        elif args[i] == "--base" and i + 1 < len(args):
            base = args[i + 1]
            i += 1
        else:
            rest.append(args[i])
        i += 1
    args = rest
    if len(args) != 1:
        print("usage: scripts/parallel-check.sh <change-dir> [--run [--base <ref>]]", file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    plan = os.path.join(change_dir, "plan.md")
    if not os.path.exists(plan):
        print("plan.md not found in %s" % args[0], file=sys.stderr)
        return 1
    parts = parallel_parts(plan)
    owners = part_owners(plan)
    if not parts:
        print("OK: plan.md does not split the work into parallel parts")
        return 0
    module_owner = {}
    for name, (files, _) in parts.items():
        for f in files:
            if f.endswith(".py"):
                module_owner[f[:-3].replace("/", ".")] = name
    problems, skipped = [], []
    for name, (_, tests) in parts.items():
        if not tests:
            problems.append("part %s lists no tests" % part_label(name, owners))
        for t in tests:
            path = os.path.join(ROOT, t)
            if not os.path.exists(path):
                problems.append("part %s: %s does not exist yet (write the tests before splitting)"
                                % (part_label(name, owners), t))
                continue
            if not t.endswith(".py"):
                skipped.append(t)
                continue
            for mod in sorted(python_imports(path)):
                other = module_owner.get(mod)
                if other and other != name:
                    problems.append("part %s: %s imports %s, which part %s builds. These tests cannot pass "
                                    "until part %s is merged. Move the shared interface into a Blocking first "
                                    "step, or test part %s through its own files only"
                                    % (part_label(name, owners), t, mod, other, other, name))
    for t in skipped:
        print("note: %s is not Python, so its imports were not checked" % t)
    if problems:
        print("FAIL: the parallel parts are not independent")
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: each part's tests import only its own files (%s)"
          % ", ".join(part_label(n, owners) for n in parts))
    if run:
        return run_parallel_isolated(change_dir, parts, base, owners)
    return 0


def git_email(root=ROOT):
    try:
        out = subprocess.run(["git", "config", "user.email"], cwd=root,
                             capture_output=True, text=True, check=False)
        return out.stdout.strip().lower()
    except OSError:
        return ""


def role_for(cfg, gate, email):
    """Return 'owner', 'cross', 'escalation' or None. Any member of a role acts for that role."""
    owner, cross = OWNERS[gate]
    roles = roles_of_email(cfg, email)
    if len(roles) != 1:
        return None  # unknown, or misconfigured pod: one person cannot hold two roles
    return {owner: "owner", cross: "cross", "escalation": "escalation"}[roles[0]]


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


def expected_emails(cfg, gate, role):
    """Emails that may sign `role` at `gate` (every member of the required pod role)."""
    owner, cross = OWNERS[gate]
    return role_emails(cfg, {"owner": owner, "cross": cross, "escalation": "escalation"}[role])


def resolve_base(base, root=ROOT):
    """origin/<base> when that ref exists, else <base>."""
    if not base.startswith("origin/") and git_out(["rev-parse", "--verify", "--quiet",
                                                   "origin/%s^{commit}" % base], root)[0] == 0:
        return "origin/" + base
    return base


def code_authors(ref, root=ROOT):
    """Author emails of the code commits in merge-base(HEAD, ref)..HEAD. A code commit touches at least
    one file outside docs/. Returns (set of emails, None), or (None, note) when there is nothing to check."""
    rc, merge_base, _ = git_out(["merge-base", "HEAD", ref], root)
    if rc != 0 or not merge_base:
        return None, "peer review skipped: no merge base between HEAD and %s" % ref
    rc, out, err = git_out(["log", "--no-merges", "--format=%x00%ae", "--name-only",
                            "%s..HEAD" % merge_base], root)
    if rc != 0:
        return None, "peer review skipped: cannot read the commits since %s (%s)" % (ref, err)
    authors = set()
    for chunk in out.split("\0")[1:]:
        lines = [l.strip() for l in chunk.strip().splitlines() if l.strip()]
        if lines and any(not f.startswith("docs/") for f in lines[1:]):
            authors.add(lines[0].lower())
    if not authors:
        return None, "peer review skipped: no code commits (outside docs/) between %s and HEAD" % ref
    return authors, None


def peer_review_problem(cfg, email, root=ROOT):
    """(refusal or None, note or None) for the gate 4 owner signature.
    With 2 or more SuperDevs, the SuperDev who signs gate 4 as owner must not have written code in the change.
    When every SuperDev wrote code, the rule falls back to the SuperBiz cross-check (as with one SuperDev)."""
    devs = role_emails(cfg, "superdev")
    if len(devs) < 2:
        return None, None
    ref = resolve_base(cfg["base_branch"], root)
    authors, note = code_authors(ref, root)
    if authors is None:
        return None, note
    free = [d for d in devs if d not in authors]
    if email not in authors:
        return None, None
    if not free:
        return None, ("peer review falls back: every SuperDev wrote code in this change (%s), so the SuperBiz "
                      "cross-check is the second pair of eyes (docs/scaling.md)" % ", ".join(sorted(authors)))
    return ("Refused: peer review. With 2 or more SuperDevs, the gate 4 owner must not have written code in "
            "this change. Code commits since %s were authored by: %s. Ask another SuperDev to sign gate 4: %s"
            % (ref, ", ".join(sorted(authors)), ", ".join(free))), None


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
        problems.extend(check_plan(artifact, cfg))
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
        want = expected_emails(cfg, gate, role)
        if e["by"] not in want:
            problems.append("gate %d: %s signed by %s, which does not match pod.yml (%s) (role mismatch)"
                            % (gate, role, e["by"], ", ".join(want) or "-"))
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
        held = roles_of_email(cfg, email)
        if len(held) > 1:
            print("Refused: git email '%s' is listed in more than one role in pod.yml (%s). "
                  "One person holds one role" % (email, ", ".join(LABEL[r] for r in held)), file=sys.stderr)
        else:
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
        plan_problems = check_plan(artifact, cfg)
        if plan_problems:
            print("Refused: plan.md does not follow the required structure, so gate 3 cannot be signed", file=sys.stderr)
            for p in plan_problems:
                print("  - " + p, file=sys.stderr)
            return 1
    if gate == 4 and role == "owner":
        refusal, note = peer_review_problem(cfg, email)
        if refusal:
            print(refusal, file=sys.stderr)
            return 1
        if note:
            print("note: " + note)
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
    if args == ["--all"]:
        errors, warnings = pod_config_problems(cfg)
        for w in warnings:
            print("Warning: " + w)
        if errors:
            failed = True
            print("FAIL pod.yml")
            for p in errors:
                print("  - " + p)
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
    signed = [parse_iso(e["at"]) for e in entries if e.get("at") and e.get("gate")]
    note = None
    if signed and min(signed) < start:
        # A squash merge drops the branch history, so the first intent.md commit on this branch
        # is later than the gates it led to. Fall back to the first signature.
        start = min(signed)
        note = "start = first gate signature (the branch history was squashed, so the intent commit time is lost)"
    print("change: %s   Risk: %s" % (os.path.basename(change_dir), risk))
    if note:
        print("note: " + note)
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
    people = {e for r in ("superbiz", "superdev", "escalation") for e in role_emails(cfg, r)}
    if email not in people:
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
            "mark-revert": cmd_mark_revert, "parallel-check": cmd_parallel_check}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
