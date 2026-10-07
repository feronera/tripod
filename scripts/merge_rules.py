#!/usr/bin/env python3
"""Risk-based merge rules (Python 3 stdlib only).

    python3 scripts/merge_rules.py auto-merge-check <change-dir> [--base main] [--record]
    python3 scripts/merge_rules.py pr-check [--author <login> --approvals <a,b> --base <ref>]
    python3 scripts/merge_rules.py sync-codeowners [--check]
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

ROOT = lib.ROOT
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def git(*args):
    res = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    return res.returncode, res.stdout


def head_sha():
    code, out = git("rev-parse", "HEAD")
    return out.strip() if code == 0 else ""


def changed_files(base, *paths):
    code, out = git("diff", "--relative", "--name-only", "%s...HEAD" % base, "--", *paths)
    if code != 0:
        return None
    return [line for line in out.splitlines() if line]


def numstat(base, *paths):
    """List of (added, deleted, path); binary files report None counts."""
    code, out = git("diff", "--relative", "--numstat", "%s...HEAD" % base, "--", *paths)
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added = int(parts[0]) if parts[0].isdigit() else None
            deleted = int(parts[1]) if parts[1].isdigit() else None
            rows.append((added, deleted, parts[2]))
    return rows


def read_review(change_dir):
    """Header keys of review.md: blockers, majors_open, second_opinion, reviewed_head."""
    path = os.path.join(change_dir, "review.md")
    if not os.path.exists(path):
        return None
    header = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s*(blockers|majors_open|second_opinion|reviewed_head)\s*:\s*(\S*)",
                         line)
            if m and m.group(1) not in header:
                header[m.group(1)] = m.group(2).strip().lower()
    return header


def review_matches_head(change_dir, reviewed):
    """reviewed_head is HEAD, or an ancestor of HEAD where later commits only touch
    this change's own folder (e.g. committing review.md or gates.log)."""
    head = head_sha()
    if not reviewed or not head:
        return False
    if reviewed == head:
        return True
    code, _ = git("merge-base", "--is-ancestor", reviewed, head)
    if code != 0:
        return False
    code, out = git("diff", "--relative", "--name-only", reviewed, head)
    if code != 0:
        return False
    own = os.path.relpath(os.path.abspath(change_dir), ROOT).replace(os.sep, "/") + "/"
    return all(f.startswith(own) for f in out.splitlines() if f)


def completed_changes(cfg, exclude):
    """Merge-ready changes (gate 4), newest first, excluding `exclude`."""
    done = []
    for d in lib.change_dirs(ROOT):
        if os.path.abspath(d) == os.path.abspath(exclude):
            continue
        if os.path.exists(os.path.join(d, "gates.log")) and not lib.check_change(d, cfg, 4):
            done.append(d)
    return sorted(done, reverse=True)


def run_tests(cfg):
    ok, _, _, _ = lib.run_test_cmd(cfg, ROOT, capture=True)
    return ok


def run_strength():
    res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "strength.py")],
                         cwd=ROOT, capture_output=True, text=True)
    return res.returncode == 0, res.stdout.strip().splitlines()


def auto_merge_reasons(change_dir, base, cfg):
    """Return the list of Thai DENY reasons (empty = ALLOW)."""
    reasons = []
    entries = lib.read_log(change_dir)
    # 1. pod setting
    if cfg["auto_merge"] != "low":
        reasons.append("pod.yml ตั้ง auto_merge: %s (ต้องเป็น low จึง merge อัตโนมัติได้)"
                       % cfg["auto_merge"])
    # 2. declared risk low and gate 1 fresh
    risk = lib.risk_of(change_dir)
    if risk != "low":
        reasons.append("Risk ใน intent.md คือ %s (merge อัตโนมัติได้เฉพาะ low)" % risk)
    if lib.check_gate(change_dir, 1, cfg, entries, risk):
        reasons.append("การอนุมัติ gate 1 ไม่ครบหรือล้าสมัย จึงยืนยันไม่ได้ว่า Risk ไม่ถูกลดหลังอนุมัติ")
    # 3. effective risk from touched paths
    files = changed_files(base)
    if files is None:
        reasons.append("เทียบกับ base '%s' ไม่ได้ (ไม่พบ branch หรือ commit นี้)" % base)
        files = []
    risky = lib.risky_files(files, ROOT)
    if risky:
        reasons.append("แตะ path อ่อนไหว: %s ระดับความเสี่ยงจริงคือ high" % ", ".join(risky))
    # 4. gates 1-3 complete and fresh
    for p in lib.check_change(change_dir, cfg, 3):
        reasons.append("gate 1-3 ยังไม่ครบ: %s" % p)
    # 5. review header
    review = read_review(change_dir)
    if review is None:
        reasons.append("ไม่พบ review.md ให้รัน /superdev:review ก่อน")
    else:
        if review.get("blockers") != "0":
            reasons.append("review.md มี blockers: %s (ต้องเป็น 0)" % review.get("blockers", "-"))
        if review.get("second_opinion") != "agree":
            reasons.append("review.md มี second_opinion: %s (ต้องเป็น agree)"
                           % review.get("second_opinion", "-"))
        if not review_matches_head(change_dir, review.get("reviewed_head", "")):
            reasons.append("review.md ตรวจ commit %s แต่ HEAD คือ %s โค้ดเปลี่ยนหลัง review ให้ review ใหม่"
                           % (review.get("reviewed_head", "-")[:12] or "-", head_sha()[:12]))
    # 6. tests and test strength (auto-merge needs a measured strength)
    tests_dir = cfg["tests_dir"]
    if not run_tests(cfg):
        reasons.append("make test ไม่ผ่าน (test_cmd: %s)" % cfg["test_cmd"])
    if cfg["strength"] == "off":
        reasons.append("test-strength ปิดอยู่ จึง merge อัตโนมัติไม่ได้")
    else:
        strong, out = run_strength()
        if not strong:
            weak = [line.split()[1] for line in out if line.startswith("WEAK ")]
            reasons.append("test-strength ไม่ผ่าน: %s"
                           % (", ".join(weak) or "ดูผลจาก scripts/test-strength.sh"))
    # 7. tests may only be added
    deleted = sum(d or 0 for _, d, _ in numstat(base, tests_dir))
    if deleted:
        reasons.append("มีการลบหรือแก้บรรทัดใน %s/ %d บรรทัด (merge อัตโนมัติอนุญาตเฉพาะการเพิ่ม test)"
                       % (tests_dir, deleted))
    # 8. diff size outside docs/ and tests_dir
    size = 0
    for added, removed, path in numstat(base):
        if path.startswith("docs/") or path.startswith(tests_dir + "/"):
            continue
        if added is None or removed is None:
            size += cfg["auto_merge_max_lines"] + 1  # binary file: never auto
        else:
            size += added + removed
    if size > cfg["auto_merge_max_lines"]:
        reasons.append("แก้โค้ดนอก docs/ และ %s/ %d บรรทัด เกิน auto_merge_max_lines (%d)"
                       % (tests_dir, size, cfg["auto_merge_max_lines"]))
    # 9. track record
    if lib.reverts(entries):
        reasons.append("change นี้มีบันทึก revert")
    need = cfg["auto_merge_min_track"]
    window = completed_changes(cfg, change_dir)[:need]
    if len(window) < need:
        reasons.append("ยังสะสมผลงานไม่ครบ %d ชิ้น (มี %d ชิ้นที่ผ่าน gate 4)" % (need, len(window)))
    reverted = [os.path.basename(d) for d in window if lib.reverts(lib.read_log(d))]
    if reverted:
        reasons.append("มีการ revert ใน %d change ล่าสุด: %s ต้องสะสมผลงานที่ไม่ถูก revert ใหม่"
                       % (need, ", ".join(reverted)))
    return reasons


def cmd_auto_merge_check(args):
    base, record, rest = "main", False, []
    i = 0
    while i < len(args):
        if args[i] == "--base" and i + 1 < len(args):
            base, i = args[i + 1], i + 2
            continue
        if args[i] == "--record":
            record = True
        else:
            rest.append(args[i])
        i += 1
    if len(rest) != 1:
        print("usage: scripts/auto-merge-check.sh <change-dir> [--base main] [--record]",
              file=sys.stderr)
        return 2
    change_dir = os.path.abspath(rest[0])
    if not os.path.isdir(change_dir):
        print("ไม่พบโฟลเดอร์ change: %s" % rest[0], file=sys.stderr)
        return 1
    cfg = lib.read_pod_yml(ROOT)
    reasons = auto_merge_reasons(change_dir, base, cfg)
    if reasons:
        print("DENY")
        for r in reasons:
            print("- " + r)
        return 1
    print("ALLOW")
    if record:
        acceptance = os.path.join(change_dir, "acceptance.md")
        blob = lib.blob_hash(acceptance) if os.path.exists(acceptance) else "-"
        line = "gate=4 role=auto by=%s at=%s blob=%s head=%s\n" % (
            lib.AUTO_BY, lib.now_iso(), blob, head_sha())
        with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write(line)
        print("บันทึกแล้ว: gate 4 role=auto (SuperBiz ต้องตรวจรับภายใน %d ชั่วโมงก่อน release)"
              % cfg["acceptance_hours"])
    return 0


# ---------- pr-check (CI on pull_request) ----------

def github_pr_context():
    """Author, approvals and base from the GitHub Actions environment (uses gh api)."""
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as fh:
        event = json.load(fh)
    pr = event["pull_request"]
    author = pr["user"]["login"]
    base = "origin/" + pr["base"]["ref"]
    repo = os.environ["GITHUB_REPOSITORY"]
    res = subprocess.run(["gh", "api", "--paginate", "repos/%s/pulls/%d/reviews" % (repo, pr["number"]),
                          "--jq", ".[] | [.user.login, .state] | @tsv"],
                         capture_output=True, text=True, check=True)
    state = {}
    for line in res.stdout.splitlines():
        login, _, st = line.partition("\t")
        if st in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            state[login.lower()] = st
    approvals = [u for u, st in state.items() if st == "APPROVED"]
    return author, approvals, base


def pr_reasons(author, approvals, base, cfg):
    """Return (effective_risk, reasons). Empty reasons = OK."""
    author = author.lower().lstrip("@")
    approvals = {a.lower().lstrip("@") for a in approvals if a}
    files = changed_files(base)
    if files is None:
        return "high", ["เทียบกับ base '%s' ไม่ได้" % base]
    dirs = sorted({os.path.join(ROOT, *f.split("/")[:3]) for f in files
                   if re.match(r"^docs/changes/\d{3}-[^/]+/", f)})
    dirs = [d for d in dirs if os.path.isdir(d)]
    reasons = []
    for d in dirs:
        if os.path.exists(os.path.join(d, "gates.log")):
            for p in lib.check_change(d, cfg):
                reasons.append("%s: %s" % (os.path.basename(d), p))
    declared = [lib.risk_of(d) for d in dirs] or ["medium"]  # no change folder: medium rules
    risk = max(declared, key=RISK_ORDER.get)
    risky = lib.risky_files(files, ROOT)
    if risky:
        risk = "high"
    auto_ok = False
    if risk == "low" and dirs and all(lib.auto_entry(lib.read_log(d)) for d in dirs):
        auto_ok = True
        for d in dirs:
            deny = auto_merge_reasons(d, base, cfg)
            if deny:
                auto_ok = False
                reasons.extend("%s: auto record ไม่ผ่าน auto-merge-check: %s" % (os.path.basename(d), r)
                               for r in deny)
    if auto_ok:
        return risk, reasons
    # The approver is never the PR author. When the agent opens PRs with SuperDev's account,
    # SuperDev cannot approve, so the other pod member's approval is the cross-check (same idea as cross-gate).
    logins = {seat: cfg.get(seat + "_github", "") for seat in ("superdev", "superbiz", "escalation")}
    for seat, login in logins.items():
        if not login:
            reasons.append("pod.yml ไม่มี %s_github" % seat)
    if reasons and any(r.startswith("pod.yml ไม่มี") for r in reasons):
        return risk, reasons
    if risk in ("low", "medium"):
        seats = ["superdev"] if logins["superdev"] != author else ["superbiz"]
    else:
        seats = [s for s in ("superdev", "superbiz", "escalation") if logins[s] != author]
    for seat in seats:
        login = logins[seat]
        if login not in approvals:
            note = " (SuperDev เป็นผู้เปิด PR จึงต้องให้ SuperBiz อนุมัติแทน)" if seat == "superbiz" and risk != "high" else ""
            reasons.append("ยังไม่มี approval จาก %s (%s) ซึ่งจำเป็นสำหรับ Risk: %s%s"
                           % (lib.LABEL[seat], login, risk, note))
    return risk, reasons


def cmd_pr_check(args):
    opts = {}
    i = 0
    while i < len(args):
        if args[i] in ("--author", "--approvals", "--base") and i + 1 < len(args):
            opts[args[i][2:]] = args[i + 1]
            i += 2
        else:
            print("usage: scripts/pr-check.sh [--author <login> --approvals <a,b> --base <ref>]",
                  file=sys.stderr)
            return 2
    if "author" in opts:
        author = opts["author"]
        approvals = [a.strip() for a in opts.get("approvals", "").split(",") if a.strip()]
        base = opts.get("base", "main")
    else:
        author, approvals, base = github_pr_context()
    cfg = lib.read_pod_yml(ROOT)
    risk, reasons = pr_reasons(author, approvals, base, cfg)
    if reasons:
        print("PR-CHECK FAIL (Risk จริง: %s)" % risk)
        for r in reasons:
            print("- " + r)
        return 1
    print("PR-CHECK OK (Risk จริง: %s)" % risk)
    return 0


# ---------- CODEOWNERS ----------

def codeowners_text(cfg):
    owners = " ".join("@" + cfg[k] for k in ("superdev_github", "escalation_github") if cfg.get(k))
    lines = ["# สร้างโดย scripts/sync-codeowners.sh จาก docs/risk-paths ห้ามแก้ไฟล์นี้เอง",
             "# path อ่อนไหวต้องได้รับ review จาก SuperDev และ escalation"]
    lines += ["%s %s" % (g, owners) for g in lib.read_risk_paths(ROOT)]
    return "\n".join(lines) + "\n"


def cmd_sync_codeowners(args):
    cfg = lib.read_pod_yml(ROOT)
    path = os.path.join(ROOT, ".github", "CODEOWNERS")
    text = codeowners_text(cfg)
    if args == ["--check"]:
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if current != text:
            print("CODEOWNERS ไม่ตรงกับ docs/risk-paths และ pod.yml ให้รัน scripts/sync-codeowners.sh")
            return 1
        print("CODEOWNERS ตรงกับ docs/risk-paths")
        return 0
    if args:
        print("usage: scripts/sync-codeowners.sh [--check]", file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("เขียน .github/CODEOWNERS แล้ว (%d path)" % len(lib.read_risk_paths(ROOT)))
    return 0


COMMANDS = {"auto-merge-check": cmd_auto_merge_check, "pr-check": cmd_pr_check,
            "sync-codeowners": cmd_sync_codeowners}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
