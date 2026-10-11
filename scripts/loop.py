#!/usr/bin/env python3
"""The loop driver for Autonomous mode (docs/autonomous.md).

    scripts/loop.sh [--dry-run] [--change NNN]

One run moves each open change on its branch (`change/NNN-slug`) by its next step: drafting and building with
the leg's agent, signing with scripts/agent-sign.sh, and merging with auto-merge-check. It stops wherever people
must act, at every limit of the sponsor, and at `loop_max_steps`. People's commands are never run here.
"""
import collections
import datetime
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity  # noqa: E402
import agent_sign  # noqa: E402
import lib  # noqa: E402
import sponsor  # noqa: E402

LOOP_AUTHOR = ("Tripod loop", "loop@tripod.invalid")
PACES = ("step", "until-blocked")
ESCALATION_STOPS = {2, 4}

State = collections.namedtuple("State", "change risk gate1 spec ux_brief gate2 plan gate3 tests build review auto "
                                        "acceptance gate4 pr_opened refused")
Step = collections.namedtuple("Step", "kind name actor")  # kind: draft | sign | build | merge | stop
LoopCfg = collections.namedtuple("LoopCfg", "on pace max_steps superceo_model lock_minutes")


# ---------- configuration ----------

def read_pod(root=lib.ROOT):
    return lib.read_pod_yml(root)


def read_loop_config(cfg):
    """(LoopCfg, problems)."""
    problems = []
    on = str(cfg.get("loop", "off") or "off").lower()
    if on not in ("on", "off"):
        problems.append("pod.yml: loop: %s is not on or off" % on)
    pace = str(cfg.get("loop_pace_low", "step") or "step").lower()
    if pace not in PACES:
        problems.append("pod.yml: loop_pace_low: %s is not step or until-blocked" % pace)
    numbers = {}
    for key, default in (("loop_max_steps", 10), ("loop_lock_minutes", 120)):
        raw = str(cfg.get(key, "") or "").strip()
        try:
            numbers[key] = int(raw) if raw else default
            if numbers[key] < 1:
                raise ValueError
        except ValueError:
            problems.append("pod.yml: %s: %s is not a number" % (key, raw))
            numbers[key] = default
    return LoopCfg(on == "on", pace, numbers["loop_max_steps"], cfg.get("superceo_model", ""),
                   numbers["loop_lock_minutes"]), problems


# ---------- the step table ----------

def next_step(state, cfg):
    """The next step of a change, from its state alone (the table in spec.md R3)."""
    low = state.risk == "low"

    def gate(n, artifact, signer_note):
        if not low:
            return Step("stop", "people sign gate %d (Risk: %s)" % (n, state.risk), "people")
        if state.refused.get(n):
            return Step("draft", "revise %s" % artifact, signer_note)
        return Step("sign", "sign gate %d" % n, "agent")

    if not state.gate1:
        return Step("stop", "people sign gate 1", "people")
    if not state.spec or not state.ux_brief:
        return Step("draft", "draft spec", "superbiz")
    if not state.gate2:
        return gate(2, "spec", "superbiz")
    if not state.plan:
        return Step("draft", "draft plan", "superdev")
    if not state.gate3:
        return gate(3, "plan", "superdev")
    if not state.tests:
        return Step("build", "write tests", "superdev")
    if not state.build:
        return Step("build", "build", "superdev")
    if not state.review:
        return Step("build", "review", "superdev")
    if not low:
        return Step("stop", "people merge (Risk: %s)" % state.risk, "people")
    if not state.auto:
        return Step("merge", "auto-merge record", "agent")
    if not state.acceptance:
        return Step("draft", "draft acceptance", "superbiz")
    if not state.gate4:
        if state.refused.get(4):
            return Step("stop", "people decide gate 4 (agents refused it)", "people")
        return Step("sign", "sign gate 4", "agent")
    if not state.pr_opened:
        return Step("merge", "open PR", "agent")
    return Step("stop", "done", "nobody")


# ---------- reading a change ----------

def git(*args, check=False):
    out = subprocess.run(["git"] + list(args), cwd=lib.ROOT, capture_output=True, text=True, check=False)
    if check and out.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), out.stderr.strip()))
    return out.returncode, out.stdout.strip()


def branch_commits(cfg, paths):
    """Commits on this branch since the base branch that touch any of `paths`."""
    base = lib.resolve_base(cfg["base_branch"])
    rc, merge_base = git("merge-base", "HEAD", base)
    if rc != 0 or not merge_base:
        return []
    rc, out = git("log", "--format=%H", "%s..HEAD" % merge_base, "--", *paths)
    return out.split() if rc == 0 else []


def last_commit_time(path):
    rc, out = git("log", "-1", "--format=%cI", "--", path)
    return sponsor.parse_at(out) if rc == 0 and out else None


def read_state(change_dir, cfg):
    name = os.path.basename(change_dir)
    has = lambda f: os.path.exists(os.path.join(change_dir, f))  # noqa: E731
    entries = lib.read_log(change_dir)
    risk = lib.risk_of(change_dir)
    complete = {n: not lib.check_gate(change_dir, n, cfg, entries, risk, release=(n == 4))
                if has(lib.ARTIFACTS[n]) else False for n in (1, 2, 3, 4)}
    records, _ = activity.read_records(os.path.join(change_dir, activity.LOG))
    refused = {}
    for n, artifact in ((2, "spec.md"), (3, "plan.md"), (4, "acceptance.md")):
        verdicts = [r for r in records if r.get("event") == "verdict" and str(r.get("gate")) == str(n)]
        if verdicts and verdicts[-1].get("verdict") == "refuse" and not complete[n]:
            changed = last_commit_time(os.path.join(change_dir, artifact))
            refused_at = sponsor.parse_at(verdicts[-1].get("at"))
            refused[n] = changed is None or refused_at is None or changed <= refused_at
    review = False
    if has("review.md"):
        import merge_rules
        head = (merge_rules.read_review(change_dir) or {}).get("reviewed_head", "")
        review = bool(head) and merge_rules.review_matches_head(change_dir, head)
    tests = bool(branch_commits(cfg, [cfg["tests_dir"]]))
    code = branch_commits(cfg, cfg["code_dirs"].split())
    return State(
        change=name, risk=risk, gate1=complete[1], spec=has("spec.md"),
        ux_brief=has("ux-brief.md") or has("spec.md"),  # the spec skill writes both; a spec alone means no UI
        gate2=complete[2], plan=has("plan.md"), gate3=complete[3], tests=tests, build=bool(code), review=review,
        auto=lib.auto_entry(entries) is not None, acceptance=has("acceptance.md"), gate4=complete[4],
        pr_opened=any(r.get("event") == "loop" and r.get("step") == "open PR" and r.get("result") == "ok"
                      for r in records),
        refused=refused)


# ---------- running steps ----------

def plugin_dir(leg):
    for base in (os.environ.get("TRIPOD_PLUGIN_DIR"), os.path.join(lib.ROOT, "plugins")):
        if base and os.path.isdir(os.path.join(base, leg)):
            return os.path.join(base, leg)
    return None


SKILLS = {"draft spec": ("superbiz", "spec", "Write spec.md and ux-brief.md in {dir}."),
          "revise spec": ("superbiz", "spec", "Revise spec.md (and ux-brief.md) in {dir} to answer every point in "
                                              "{dir}/refusals.md, the reasons the gate 2 check gave."),
          "draft plan": ("superdev", "plan", "Write plan.md in {dir}."),
          "revise plan": ("superdev", "plan", "Revise plan.md in {dir} to answer every point in {dir}/refusals.md, "
                                              "the reasons the gate 3 check gave."),
          "write tests": ("superdev", "test-first", "Write the failing tests for {dir} from spec.md and plan.md."),
          "build": ("superdev", "build", "Build {dir} until make test passes. Tests are locked: do not edit them."),
          "review": ("superdev", "review", "Review the change {dir} and write review.md with its header."),
          "draft acceptance": ("superbiz", "acceptance", "Write acceptance.md in {dir} from the demo steps in "
                                                         "plan.md and review.md.")}


def agent_prompt(step_name, change_dir):
    leg, skill, task = SKILLS[step_name]
    rel = os.path.relpath(change_dir, lib.ROOT)
    return "\n".join([
        "You are the %s agent of this pod, working with no person present." % lib.LABEL[leg],
        "Use the %s skill (/%s:%s). %s" % (skill, leg, skill, task.format(dir=rel)),
        "Do not ask questions. Decide what you can and say why; accept the rest as a risk with a reason. Gates "
        "already passed were verified by scripts/gate-check.sh: do not ask anyone to check them again. Keep the "
        "artifact short.",
        "Edit only the files this step needs. Do not sign gates or record approvals: that is not this step's job.",
    ])


def allowed_paths(step_name, change_dir, cfg):
    rel = os.path.relpath(change_dir, lib.ROOT)
    paths = ["%s/**" % rel]
    if step_name in ("write tests",):
        paths.append("%s/**" % cfg["tests_dir"])
    if step_name == "build":
        paths += ["%s/**" % d for d in cfg["code_dirs"].split()]
    return paths


def run_agent(step_name, change_dir, cfg, timeout):
    leg = SKILLS[step_name][0]
    folder = plugin_dir(leg)
    if folder is None:
        return False, "the %s plugin was not found (plugins/%s or TRIPOD_PLUGIN_DIR)" % (leg, leg)
    edits = allowed_paths(step_name, change_dir, cfg)
    allowed = ["Read", "Grep", "Glob", "Skill"] + ["Edit(%s)" % p for p in edits] + ["Write(%s)" % p for p in edits]
    tools = "Read,Grep,Glob,Skill,Edit,Write"  # Skill loads the plugin's skills
    if SKILLS[step_name][0] == "superdev" and step_name in ("write tests", "build", "review"):
        allowed += ["Bash(make test)", "Bash(make check)", "Bash(git diff:*)", "Bash(git status)",
                    "Bash(git log:*)", "Bash(scripts/test-strength.sh)"]
        tools += ",Bash"
    cmd = [os.environ.get("TRIPOD_CLAUDE", "claude"), "-p", agent_prompt(step_name, change_dir),
           "--model", cfg["%s_agent_model" % leg], "--plugin-dir", folder, "--output-format", "json",
           "--tools", tools, "--allowedTools", ",".join(allowed)]
    try:
        out = subprocess.run(cmd, cwd=lib.ROOT, capture_output=True, text=True, timeout=timeout,
                             stdin=subprocess.DEVNULL, check=False)
    except FileNotFoundError:
        return False, "claude is not installed"
    except subprocess.TimeoutExpired:
        return False, "no answer within %d s" % timeout
    if out.returncode != 0:
        return False, "claude exited %d" % out.returncode
    return True, ""


def changed_paths():
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=lib.ROOT,
                         capture_output=True, text=True, check=False)  # unstripped: the first column matters
    paths = [l[3:] for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []
    # .pod/ is local state; docs/superceo/ and docs/digest/ are written by the sponsor's tools before a run
    return [p for p in paths if not p.startswith((".pod/", "docs/superceo/", "docs/digest/"))]


def discard(paths):
    """Undo an agent's edits to `paths` after a failed step (the run started from a clean tree)."""
    for p in paths:
        rc, _ = git("ls-files", "--error-unmatch", p)
        if rc == 0:
            git("checkout", "--", p)
        elif os.path.exists(os.path.join(lib.ROOT, p)):
            os.remove(os.path.join(lib.ROOT, p))


def commit(message, paths):
    """Commit only `paths` (the step's own files), as the loop's author."""
    env = dict(os.environ, GIT_AUTHOR_NAME=LOOP_AUTHOR[0], GIT_AUTHOR_EMAIL=LOOP_AUTHOR[1],
               GIT_COMMITTER_NAME=LOOP_AUTHOR[0], GIT_COMMITTER_EMAIL=LOOP_AUTHOR[1])
    subprocess.run(["git", "add", "-A", "--"] + list(paths), cwd=lib.ROOT, check=False, capture_output=True)
    out = subprocess.run(["git", "commit", "-q", "-m", message], cwd=lib.ROOT, env=env, capture_output=True,
                         text=True, check=False)
    return out.returncode == 0


def run_tests(cfg):
    import merge_rules  # the kit's own test runner (test_cmd from pod.yml)
    return merge_rules.run_tests(cfg)


def draft_or_build(step, change_dir, cfg, timeout):
    """(ok, reason, paths): the step's own changed files, to commit with its record (only when make test passes,
    for the build step). Nothing is committed here."""
    rel = os.path.relpath(change_dir, lib.ROOT)
    if step.name in ("build",):
        os.makedirs(os.path.join(lib.ROOT, ".pod"), exist_ok=True)
        open(os.path.join(lib.ROOT, ".pod", "lock-tests"), "a").close()
    ok, reason = run_agent(step.name, change_dir, cfg, timeout)
    changed = changed_paths()
    allowed = [p.rstrip("*").rstrip("/") for p in allowed_paths(step.name, change_dir, cfg)]
    outside = [p for p in changed if not any(p == a or p.startswith(a + "/") for a in allowed)]
    own = [p for p in changed if p not in outside]
    if not ok:
        discard(changed)
        return False, reason, []
    if outside:
        discard(changed)
        return False, "the agent changed files outside this step (%s)" % ", ".join(outside[:3]), []
    work = [p for p in own if not p.endswith(activity.LOG)]
    if not work:
        discard(changed)
        return False, "the agent wrote nothing", []
    if step.name == "draft spec" and not os.path.exists(os.path.join(change_dir, "spec.md")):
        discard(changed)
        return False, "spec.md was not written", []
    if step.name in ("build",) and not run_tests(cfg):
        discard(changed)
        return False, "make test fails after the build", []
    if step.name == "write tests":
        os.makedirs(os.path.join(lib.ROOT, ".pod"), exist_ok=True)
        open(os.path.join(lib.ROOT, ".pod", "lock-tests"), "a").close()
    return True, rel, own


def sign(change_dir, gate):
    """(ok, label, reasons) from scripts/agent-sign.sh."""
    out = subprocess.run([os.path.join(lib.ROOT, "scripts", "agent-sign.sh"), change_dir, str(gate)],
                         cwd=lib.ROOT, capture_output=True, text=True, check=False)
    text = out.stdout + out.stderr
    m = re.search(r"^(APPROVE|REFUSE) gate %d (owner|cross)" % gate, text, re.M)
    if out.returncode == 0 and m:
        return True, "%s → APPROVE" % m.group(2), ""
    if m:
        with open(os.path.join(change_dir, "refusals.md"), "a", encoding="utf-8") as fh:
            fh.write("## Gate %d %s, %s\n\n%s\n\n" % (gate, m.group(2), sponsor.now().isoformat(timespec="seconds"),
                                                       text.strip()))
        return False, "refused", text.strip().splitlines()[0] if text.strip() else ""
    first = next((l for l in text.splitlines() if l.startswith(("Refused", "agent-sign"))), text.strip()[:200])
    return False, "not started", first


def gh_path():
    path = os.environ.get("TRIPOD_GH") or shutil.which("gh")
    return path if path and os.path.exists(path) else None


def merge_step(step, change_dir, cfg):
    """(ok, label, reason) for the auto-merge record and for opening the PR."""
    base = lib.resolve_base(cfg["base_branch"])
    if step.name == "auto-merge record":
        out = subprocess.run([os.path.join(lib.ROOT, "scripts", "auto-merge-check.sh"), change_dir, "--base", base,
                              "--record"], cwd=lib.ROOT, capture_output=True, text=True, check=False)
        if out.returncode != 0:
            reasons = [l[2:] for l in out.stdout.splitlines() if l.startswith("- ")]
            return False, "", "people merge: %s" % (reasons[0] if reasons else "auto-merge-check said DENY")
        commit("loop(%s): auto-merge record" % os.path.basename(change_dir)[:3], [change_dir])
        return True, "ALLOW", ""
    gh = gh_path()
    if gh is None:
        return False, "", "ready to merge: push the branch and open the PR (gh not available)"
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    rc, _ = git("push", "-u", "origin", branch)
    if rc != 0:
        return False, "", "push failed; ready to merge by hand"
    subprocess.run([gh, "pr", "create", "--fill", "--base", cfg["base_branch"]], cwd=lib.ROOT, capture_output=True,
                   check=False)
    out = subprocess.run([gh, "pr", "merge", "--auto", "--squash"], cwd=lib.ROOT, capture_output=True, text=True,
                         check=False)
    if out.returncode != 0:
        return False, "", "PR opened; auto-merge could not be turned on (%s)" % out.stderr.strip()[:120]
    return True, "PR opened with auto-merge", ""


# ---------- one run ----------

def record(change_dir, run_id, step, result, reason=""):
    with open(os.path.join(change_dir, activity.LOG), "a", encoding="utf-8") as fh:
        fh.write(activity.format_record({"event": "loop", "at": sponsor.now().isoformat(timespec="seconds"),
                                         "run": run_id, "step": step, "result": result, "reason": reason}))


def last_loop_record(change_dir):
    records, _ = activity.read_records(os.path.join(change_dir, activity.LOG))
    loops = [r for r in records if r.get("event") == "loop"]
    return loops[-1] if loops else None


def change_branches():
    rc, out = git("for-each-ref", "--format=%(refname:short)", "refs/heads/change/")
    names = [b[len("change/"):] for b in out.splitlines() if re.match(r"^change/\d{3}-", b)] if rc == 0 else []
    return sorted(names)


def priority_order(names):
    path = os.path.join(lib.ROOT, "docs", "superceo", sponsor.now().strftime("%Y-%m-%d") + ".md")
    if not os.path.exists(path):
        return names
    text = open(path, encoding="utf-8").read()
    return sorted(names, key=lambda n: (text.find(n) if n in text else len(text) + 1, n))


def refuse(message):
    print("Refused: " + message)
    return 1


def main(args):
    dry = "--dry-run" in args
    only = args[args.index("--change") + 1] if "--change" in args and args.index("--change") + 1 < len(args) else None
    cfg = read_pod()
    loop_cfg, problems = read_loop_config(cfg)
    limits, limit_problems = sponsor.read_limits(cfg)
    if problems or limit_problems:
        return refuse("pod.yml has problems:\n  - " + "\n  - ".join(problems + limit_problems))
    if cfg["mode"] != "autonomous":
        return refuse("the loop runs only in mode: autonomous")
    if not loop_cfg.on:
        return refuse("pod.yml sets loop: off. The sponsor turns the loop on with loop: on")
    if os.path.exists(os.path.join(lib.ROOT, ".pod", "kill-switch")):
        return refuse("kill switch is on (.pod/kill-switch)")
    if changed_paths():
        return refuse("the working tree has uncommitted changes; commit or stash them first")
    lock = os.path.join(lib.ROOT, ".pod", "loop.lock")
    if os.path.exists(lock):
        started = sponsor.parse_at(open(lock, encoding="utf-8").read().strip())
        age = (sponsor.now() - started) if started else None
        stale = age is not None and age > datetime.timedelta(minutes=loop_cfg.lock_minutes)
        return refuse("another loop run holds .pod/loop.lock (started %s ago%s)" % (
            str(age).split(".")[0] if age else "an unknown time", "; it looks stale: a person removes it" if stale else ""))
    names = [n for n in priority_order(change_branches()) if not only or n.startswith(only)]
    if not names:
        print("Loop: nothing to do (no open changes past gate 1)")
        return 0
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    with open(lock, "w", encoding="utf-8") as fh:
        fh.write(sponsor.now().isoformat())
    _, home = git("rev-parse", "--abbrev-ref", "HEAD")
    run_id = sponsor.now().strftime("%Y%m%dT%H%M%S")
    steps = stops = 0
    stop_reasons = collections.Counter()
    try:
        print("Loop run %s UTC%s" % (sponsor.fmt_time(sponsor.now()), " (dry run)" if dry else ""))
        for name in names:
            if steps >= loop_cfg.max_steps:
                print("Loop: stopped at loop_max_steps (%d)" % loop_cfg.max_steps)
                break
            rc, _ = git("checkout", "-q", "change/%s" % name)
            change_dir = os.path.join(lib.CHANGES_DIR, name)
            if rc != 0 or not os.path.isdir(change_dir):
                print("%s: stopped: branch change/%s not found" % (name, name))
                continue
            taken = 0
            while True:
                cfg = read_pod()
                state = read_state(change_dir, cfg)
                step = next_step(state, cfg)
                if dry:
                    actor = step.actor
                    if step.kind == "sign":
                        gate = int(step.name.split()[-1])
                        role = agent_sign.next_role(lib.read_log(change_dir), gate,
                                                    lib.blob_hash(os.path.join(change_dir, lib.ARTIFACTS[gate])))
                        actor = "agent:%s" % lib.OWNERS[gate][0 if role == "owner" else 1]
                    elif step.actor in ("superbiz", "superdev"):
                        actor = "agent:%s" % step.actor
                    print("%s (%s): next: %s (%s)" % (name, state.risk, step.name, actor))
                    break
                stop = None
                if step.kind == "stop":
                    stop = step.name
                elif os.path.exists(os.path.join(lib.ROOT, ".pod", "kill-switch")):
                    stop = "kill switch is on (.pod/kill-switch)"
                else:
                    at = sponsor.now()
                    events, _ = sponsor.ledger(lib.ROOT, at, cfg)
                    gate = int(step.name.split()[-1]) if step.kind == "sign" else 2
                    stopped = sponsor.stops(events, limits, name, gate, at)
                    if stopped:
                        stop = stopped[0]
                if stop is None and steps >= loop_cfg.max_steps:
                    print("%s: stopped: loop_max_steps (%d) reached for this run" % (name, loop_cfg.max_steps))
                    break
                if stop is not None:
                    if step.kind == "stop" and state.risk == "high" and step.name.startswith("people sign gate"):
                        maybe_brief(change_dir, int(step.name.split()[3]))
                    last = last_loop_record(change_dir)
                    if not (last and last.get("result") == "stop" and last.get("reason") == stop):
                        record(change_dir, run_id, step.name, "stop", stop)
                        commit("loop(%s): stopped" % name[:3], [change_dir])
                    print("%s: stopped: %s" % (name, stop))
                    stops += 1
                    stop_reasons[stop.split(":")[0]] += 1
                    break
                label, ok, reason, paths = step.name, True, "", []
                print("%s: %s (%s)..." % (name, step.name, step.actor), flush=True)
                if step.kind in ("draft", "build"):
                    ok, reason, paths = draft_or_build(step, change_dir, cfg, cfg["agent_sign_timeout"])
                    if not ok:
                        reason = "%s failed (%s); nothing was committed" % (step.name, reason)
                elif step.kind == "sign":
                    gate = int(step.name.split()[-1])
                    ok, outcome, why = sign(change_dir, gate)
                    label = "%s %s" % (step.name, outcome)
                    if not ok:
                        reason = "%s %s" % (step.name, outcome if outcome == "refused" else "not started: " + why)
                elif step.kind == "merge":
                    ok, outcome, reason = merge_step(step, change_dir, cfg)
                    label = "%s → %s" % (step.name, outcome) if ok else step.name
                if not ok:
                    record(change_dir, run_id, step.name, "refused" if "refused" in reason else "failed", reason)
                    commit("loop(%s): stopped" % name[:3], [change_dir])
                    print("%s: stopped: %s" % (name, reason))
                    stops += 1
                    stop_reasons[step.name] += 1
                    break
                record(change_dir, run_id, step.name, "ok")
                commit("loop(%s): %s" % (name[:3], step.name), [change_dir] + paths)
                print("%s: %s" % (name, label))
                steps += 1
                taken += 1
                if state.risk != "low" or loop_cfg.pace == "step":
                    break
    finally:
        git("checkout", "-q", home)
        if os.path.exists(lock):
            os.remove(lock)
    if not dry:
        print("Loop run: %d steps, %d stops%s" % (steps, stops, " (%s)" % ", ".join(
            "%s %d" % (k, v) for k, v in stop_reasons.items()) if stop_reasons else ""))
    return 0


def maybe_brief(change_dir, gate):
    """SuperCEO writes a brief for a high-risk change waiting for people at an escalation gate (R13)."""
    if gate not in ESCALATION_STOPS:
        return
    artifact = os.path.join(change_dir, lib.ARTIFACTS[gate])
    blob = lib.blob_hash(artifact) if os.path.exists(artifact) else "-"
    brief = os.path.join(change_dir, "brief.md")
    if os.path.exists(brief) and ("artifact_blob: %s" % blob) in open(brief, encoding="utf-8").read():
        return
    subprocess.run([os.path.join(lib.ROOT, "scripts", "superceo.sh"), "brief", change_dir], cwd=lib.ROOT,
                   capture_output=True, check=False)
    if os.path.exists(brief):
        commit("loop(%s): SuperCEO brief" % os.path.basename(change_dir)[:3], [change_dir])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
