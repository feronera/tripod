#!/usr/bin/env python3
"""The loop for Autonomous mode: the document stages (docs/autonomous.md).

    scripts/loop.sh [--dry-run] [--change NNN-slug]

One run gives each open change (branch `change/NNN-slug`) one next step: draft spec.md and ux-brief.md, sign
gate 2, draft plan.md, sign gate 3. Then it stops: people build. Agents work in an isolated session and may edit
only the step's artifact files. People's commands, building and merging are never run here.
"""
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity  # noqa: E402
import agent_sign  # noqa: E402
import lib  # noqa: E402
import sponsor  # noqa: E402

LOOP_AUTHOR = ("Tripod loop", "loop@tripod.invalid")
State = collections.namedtuple("State", "change risk gate1 spec gate2 plan gate3 refused")
Step = collections.namedtuple("Step", "kind name actor")  # kind: draft | sign | stop
LoopCfg = collections.namedtuple("LoopCfg", "on max_steps superceo_model")

ARTIFACTS = {"draft spec": ("superbiz", "spec", ("spec.md", "ux-brief.md")),
             "revise spec": ("superbiz", "spec", ("spec.md", "ux-brief.md")),
             "draft plan": ("superdev", "plan", ("plan.md",)),
             "revise plan": ("superdev", "plan", ("plan.md",))}


# ---------- configuration ----------

def read_loop_config(cfg):
    """(LoopCfg, problems)."""
    problems = []
    on = str(cfg.get("loop", "off") or "off").lower()
    if on not in ("on", "off"):
        problems.append("pod.yml: loop: %s is not on or off" % on)
    raw = str(cfg.get("loop_max_steps", "") or "").strip()
    max_steps = 10
    if raw:
        try:
            value = int(raw) if re.fullmatch(r"-?[0-9]+", raw) else None
        except ValueError:
            value = None
        if value is None:
            problems.append("pod.yml: loop_max_steps: %s is not a number" % raw)
        elif value < 1:
            problems.append("pod.yml: loop_max_steps: %s must be 1 or more" % raw)
        else:
            max_steps = value
    return LoopCfg(on == "on", max_steps, cfg.get("superceo_model", "")), problems


# ---------- the step table ----------

def next_step(state):
    """The next step of a change, from its state alone (spec R3)."""
    def gate(n, artifact, owner):
        if state.risk != "low":
            return Step("stop", "people sign gate %d (Risk: %s)" % (n, state.risk), "people")
        if state.refused.get(n):
            return Step("draft", "revise %s" % artifact, owner)
        return Step("sign", "sign gate %d" % n, "agent")

    if not state.gate1:
        return Step("stop", "people sign gate 1", "people")
    if not state.spec:
        return Step("draft", "draft spec", "superbiz")
    if not state.gate2:
        return gate(2, "spec", "superbiz")
    if not state.plan:
        return Step("draft", "draft plan", "superdev")
    if not state.gate3:
        return gate(3, "plan", "superdev")
    return Step("stop", "people build (gate 3 is complete)", "people")


# ---------- git and state ----------

def git(*args):
    out = subprocess.run(["git", "-c", "core.quotePath=false"] + list(args), cwd=lib.ROOT, capture_output=True,
                         text=True, check=False)
    return out.returncode, out.stdout.strip()


def changed_paths(sponsor_outputs=False):
    """Uncommitted and new files (git status read unstripped: its first column matters). .pod/ is local state.
    docs/superceo/ and docs/digest/ are written by the sponsor's tools before a run, so they do not make the tree
    dirty; inside a step they count like any other file (sponsor_outputs=True)."""
    out = subprocess.run(["git", "-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"],
                         cwd=lib.ROOT, capture_output=True, text=True, check=False)
    paths = [l[3:] for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []
    skip = (".pod/",) if sponsor_outputs else (".pod/", "docs/superceo/", "docs/digest/")
    return [p for p in paths if not p.startswith(skip)]


def read_state(change_dir, cfg):
    has = lambda f: os.path.exists(os.path.join(change_dir, f))  # noqa: E731
    entries = lib.read_log(change_dir)
    risk = lib.risk_of(change_dir)
    complete = {n: has(lib.ARTIFACTS[n]) and not lib.check_gate(change_dir, n, cfg, entries, risk) for n in (1, 2, 3)}
    records, _ = activity.read_records(os.path.join(change_dir, activity.LOG))
    refused = {}
    for n, artifact in ((2, "spec.md"), (3, "plan.md")):
        verdicts = [r for r in records if r.get("event") == "verdict" and str(r.get("gate")) == str(n)]
        if verdicts and verdicts[-1].get("verdict") == "refuse" and not complete[n]:
            rc, when = git("log", "-1", "--format=%cI", "--", os.path.join(change_dir, artifact))
            changed = sponsor.parse_at(when) if rc == 0 and when else None
            refused_at = sponsor.parse_at(verdicts[-1].get("at"))
            refused[n] = changed is None or refused_at is None or changed <= refused_at
    return State(os.path.basename(change_dir), risk, complete[1], has("spec.md"), complete[2], has("plan.md"),
                 complete[3], refused)


def base_rules(cfg):
    """(base ref, risk globs) read once from the home checkout and the base branch, before any change branch is
    checked out, so no branch can change them for itself."""
    base = lib.resolve_base(cfg["base_branch"])
    rc, text = git("show", "%s:docs/risk-paths" % base)
    globs = [l.split("#", 1)[0].strip() for l in (text.splitlines() if rc == 0 else []) if l.split("#", 1)[0].strip()]
    return base, globs


def branch_stop(name, base, globs, limits):
    """A reason the loop must not work on this branch, or None (spec R6). A branch may change only its own change
    folder; then the scripts, plugins and pod.yml the loop runs are exactly the base branch's."""
    rc, merge_base = git("merge-base", "HEAD", base)
    if rc != 0 or not merge_base:
        return "the branch has no common history with %s; people take this change" % base
    _, committed = git("diff", "--no-renames", "--name-only", merge_base)
    files = sorted(set(committed.splitlines()) | set(changed_paths()))
    risky = [f for f in files if any(lib.path_matches(f, g) for g in globs)]
    if risky:
        return "the branch touches a sensitive path (%s); people take this change" % ", ".join(risky[:3])
    governance = lib.governance_files(files)
    if governance:
        return "the branch edits agent instructions or gate rules (%s); people take this change" % ", ".join(
            governance[:3])
    banned = sponsor.forbidden_files(files, limits)
    if banned:
        return "the branch touches %s, which agents may not change (agent_forbidden_paths)" % ", ".join(banned[:3])
    own = "docs/changes/%s/" % name
    _, staged = git("ls-files", "-s", "--", own)
    links = [l.split("\t", 1)[-1] for l in staged.splitlines() if not l.startswith("100")]
    links += [os.path.join(own, f) for f in os.listdir(os.path.join(lib.ROOT, own))
              if os.path.islink(os.path.join(lib.ROOT, own, f))] if os.path.isdir(os.path.join(lib.ROOT, own)) else []
    if links:
        return "the change folder holds links or other non-regular files (%s); people take this change" % ", ".join(
            sorted(set(links))[:3])
    outside = [f for f in files if not f.startswith(own)]
    if outside:
        return "the branch changes files outside %s (%s); people take this change" % (own, ", ".join(outside[:3]))
    return None


# ---------- steps ----------

def plugin_dir(leg):
    for base in (os.environ.get("TRIPOD_PLUGIN_DIR"), os.path.join(lib.ROOT, "plugins")):
        if base and os.path.isdir(os.path.join(base, leg)):
            return os.path.join(base, leg)
    return None


def agent_env():
    """The agent's environment: no access tokens or secrets (lib.agent_env), and the loop's git identity."""
    return lib.agent_env(dict(GIT_AUTHOR_NAME=LOOP_AUTHOR[0], GIT_AUTHOR_EMAIL=LOOP_AUTHOR[1],
                              GIT_COMMITTER_NAME=LOOP_AUTHOR[0], GIT_COMMITTER_EMAIL=LOOP_AUTHOR[1]))


def run_agent(step, change_dir, cfg):
    leg, skill, files = ARTIFACTS[step.name]
    folder = plugin_dir(leg)
    if folder is None:
        return False, "the %s plugin was not found" % leg
    rel = os.path.relpath(change_dir, lib.ROOT)
    paths = [os.path.join(rel, f) for f in files]
    revise = "Revise %s to answer every point in %s/refusals.md, the reasons the last check gave. " % (
        " and ".join(files), rel) if step.name.startswith("revise") else ""
    prompt = "\n".join([
        "You are the %s agent of this pod, working with no person present." % lib.LABEL[leg],
        "Use the %s skill (/%s:%s) for %s. %sWrite only: %s." % (skill, leg, skill, rel, revise, ", ".join(paths)),
        "Do not ask questions. Decide what you can and say why; accept the rest as a risk with a reason. Gates "
        "already passed were verified by scripts/gate-check.sh. Keep the artifact short.",
    ])
    allowed = ["Read", "Grep", "Glob", "Skill"] + ["%s(%s)" % (t, p) for p in paths for t in ("Edit", "Write")]
    cmd = [os.environ.get("TRIPOD_CLAUDE", "claude"), "-p", prompt, "--model", cfg["%s_agent_model" % leg],
           "--plugin-dir", folder, "--output-format", "json", "--setting-sources", "", "--strict-mcp-config",
           "--tools", "Read,Grep,Glob,Skill,Edit,Write", "--allowedTools", ",".join(allowed)]
    try:
        out = subprocess.run(cmd, cwd=lib.ROOT, env=agent_env(), capture_output=True, text=True,
                             timeout=cfg["agent_sign_timeout"], stdin=subprocess.DEVNULL, check=False)
    except FileNotFoundError:
        return False, "claude is not installed"
    except subprocess.TimeoutExpired:
        return False, "no answer within %d s" % cfg["agent_sign_timeout"]
    if out.returncode != 0:
        return False, "claude exited %d" % out.returncode
    return True, ""


def draft(step, change_dir, cfg):
    """(ok, reason, files). Work the agent committed itself counts; every file changed since the step began must
    be one of the step's artifacts (or activity.log, which the plugin's hook appends to). Otherwise the branch
    goes back to where the step started."""
    rel = os.path.relpath(change_dir, lib.ROOT)
    log_rel = os.path.join(rel, activity.LOG)
    allowed = {os.path.join(rel, f) for f in ARTIFACTS[step.name][2]} | {log_rel}
    _, start = git("rev-parse", "HEAD")
    before = set(changed_paths(sponsor_outputs=True))  # untracked files that are not the agent's: never removed
    log_path = os.path.join(lib.ROOT, log_rel)
    log_before = open(log_path, encoding="utf-8").read() if os.path.exists(log_path) else ""
    ok, reason = run_agent(step, change_dir, cfg)
    _, committed = git("diff", "--no-renames", "--name-only", start)
    touched = sorted(set(committed.splitlines()) | (set(changed_paths(sponsor_outputs=True)) - before))
    outside = [p for p in touched if p not in allowed]
    log_now = open(log_path, encoding="utf-8").read() if os.path.exists(log_path) else ""
    if not log_now.startswith(log_before):
        outside.append(log_rel + " (rewritten, not appended)")

    def undo(why):
        git("reset", "-q", "--hard", start)
        for p in set(changed_paths(sponsor_outputs=True)) - before:
            full = os.path.join(lib.ROOT, p)
            if os.path.isfile(full) and not os.path.islink(full):
                os.remove(full)
        return False, why, []

    if not ok:
        return undo(reason)
    if outside:
        return undo("the agent changed files outside this step (%s)" % ", ".join(outside[:3]))
    work = [p for p in touched if not p.endswith(activity.LOG)]
    if not work:
        return undo("the agent wrote nothing")
    git("reset", "-q", "--soft", start)  # one commit per step, made by the loop
    return True, "", touched


def sign(change_dir, gate):
    """(ok, label, reason) from agent-sign."""
    out = subprocess.run([os.path.join(lib.ROOT, "scripts", "agent-sign.sh"), change_dir, str(gate)], cwd=lib.ROOT,
                         env=agent_env(), capture_output=True, text=True, check=False)
    text = (out.stdout + out.stderr).strip()
    m = re.search(r"^(APPROVE|REFUSE) gate %d (owner|cross)" % gate, text, re.M)
    if out.returncode == 0 and m:
        return True, "%s → APPROVE" % m.group(2), ""
    if m:
        with open(os.path.join(change_dir, "refusals.md"), "a", encoding="utf-8") as fh:
            fh.write("## Gate %d %s, %s\n\n%s\n\n" % (gate, m.group(2), sponsor.now().isoformat(timespec="seconds"),
                                                       text))
        return False, "refused", "sign gate %d refused" % gate
    first = next((l for l in text.splitlines() if l.startswith(("Refused", "agent-sign"))), text[:200])
    return False, "not started", "sign gate %d not started: %s" % (gate, first)


def commit(message, paths):
    env = dict(os.environ, GIT_AUTHOR_NAME=LOOP_AUTHOR[0], GIT_AUTHOR_EMAIL=LOOP_AUTHOR[1],
               GIT_COMMITTER_NAME=LOOP_AUTHOR[0], GIT_COMMITTER_EMAIL=LOOP_AUTHOR[1])
    subprocess.run(["git", "add", "-A", "--"] + list(paths), cwd=lib.ROOT, capture_output=True, check=False)
    out = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", message], cwd=lib.ROOT,
                         env=env, capture_output=True, text=True, check=False)
    return out.returncode == 0 or "nothing to commit" in out.stdout + out.stderr


def record(change_dir, run_id, step, result, reason=""):
    with open(os.path.join(change_dir, activity.LOG), "a", encoding="utf-8") as fh:
        fh.write(activity.format_record({"event": "loop", "at": sponsor.now().isoformat(timespec="seconds"),
                                         "run": run_id, "step": step, "result": result, "reason": reason}))


def last_loop_record(change_dir):
    records, _ = activity.read_records(os.path.join(change_dir, activity.LOG))
    loops = [r for r in records if r.get("event") == "loop"]
    return loops[-1] if loops else None


def maybe_brief(change_dir):
    """SuperCEO briefs people on a high-risk change waiting at gate 2 (spec R13), once per artifact version."""
    spec = os.path.join(change_dir, "spec.md")
    blob = lib.blob_hash(spec) if os.path.exists(spec) else "-"
    brief = os.path.join(change_dir, "brief.md")
    if os.path.exists(brief) and ("artifact_blob: %s" % blob) in open(brief, encoding="utf-8").read():
        return False
    subprocess.run([os.path.join(lib.ROOT, "scripts", "superceo.sh"), "brief", change_dir], cwd=lib.ROOT,
                   env=agent_env(), capture_output=True, check=False)
    return os.path.exists(brief)


# ---------- one run ----------

def change_branches():
    rc, out = git("for-each-ref", "--format=%(refname:short)", "refs/heads/change/")
    return sorted(b[len("change/"):] for b in out.splitlines() if re.match(r"^change/\d{3}-", b)) if rc == 0 else []


def priority_order(names):
    """Today's SuperCEO order: the first line of the priorities file that names each change."""
    path = os.path.join(lib.ROOT, "docs", "superceo", sponsor.now().strftime("%Y-%m-%d") + ".md")
    if not os.path.exists(path):
        return names
    lines = open(path, encoding="utf-8").read().splitlines()
    rank = {n: next((i for i, l in enumerate(lines) if n in l), len(lines)) for n in names}
    return sorted(names, key=lambda n: (rank[n], n))


def take_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as fh:
        fh.write(sponsor.now().isoformat())
    return True


def refuse(message):
    print("Refused: " + message)
    return 1


def main(args):
    dry = "--dry-run" in args
    only = args[args.index("--change") + 1] if "--change" in args and args.index("--change") + 1 < len(args) else None
    cfg = lib.read_pod_yml()
    loop_cfg, problems = read_loop_config(cfg)
    limits, limit_problems = sponsor.read_limits(cfg)
    if problems or limit_problems:
        return refuse("pod.yml has problems:\n  - " + "\n  - ".join(problems + limit_problems))
    if cfg["mode"] != "autonomous":
        return refuse("the loop runs only in mode: autonomous")
    if not loop_cfg.on:
        return refuse("pod.yml sets loop: off. The sponsor turns the loop on with loop: on")
    kill = os.path.join(lib.ROOT, ".pod", "kill-switch")
    if os.path.exists(kill):
        return refuse("kill switch is on (.pod/kill-switch)")
    if changed_paths():
        return refuse("the working tree has uncommitted changes; commit or stash them first")
    lock = os.path.join(lib.ROOT, ".pod", "loop.lock")
    if not take_lock(lock):
        started = sponsor.parse_at(open(lock, encoding="utf-8").read().strip())
        age = str(sponsor.now() - started).split(".")[0] if started else "an unknown time"
        return refuse("another loop run holds .pod/loop.lock (started %s ago; a person removes it if it is stale)"
                      % age)
    _, home = git("rev-parse", "--abbrev-ref", "HEAD")
    if home == "HEAD":
        _, home = git("rev-parse", "HEAD")  # detached: come back to the same commit
    try:
        base, globs = base_rules(cfg)  # read once, before any change branch is checked out
    except Exception:
        os.remove(lock)
        raise
    plain = base[len("origin/"):] if base.startswith("origin/") else base
    if plain.startswith("change/"):
        os.remove(lock)
        return refuse("base_branch: %s is a change branch; the base must be the shared branch changes merge into "
                      "(pod.yml base_branch, default main)" % plain)
    run_id = sponsor.now().strftime("%Y%m%dT%H%M%S")
    steps = stops = 0
    try:
        names = [n for n in priority_order(change_branches()) if not only or n == only]
        if not names:
            print("Loop: nothing to do (no open change branches)")
            return 0
        print("Loop run %s UTC%s" % (sponsor.fmt_time(sponsor.now()), " (dry run)" if dry else ""))
        for name in names:
            if steps >= loop_cfg.max_steps:
                print("Loop: stopped at loop_max_steps (%d)" % loop_cfg.max_steps)
                break
            rc, _ = git("checkout", "-q", "change/%s" % name)
            if rc != 0:
                print("%s: skipped: branch change/%s could not be checked out" % (name, name))
                git("checkout", "-q", home)
                continue
            change_dir = os.path.join(lib.CHANGES_DIR, name)
            if not os.path.exists(os.path.join(change_dir, "intent.md")):
                print("%s: skipped: no docs/changes/%s/intent.md on its branch" % (name, name))
                continue
            if changed_paths():
                print("%s: skipped: files left over after checking out the branch (%s); a person cleans up"
                      % (name, ", ".join(changed_paths()[:3])))
                continue
            state = read_state(change_dir, cfg)  # cfg is the home pod.yml, read before any checkout
            step = next_step(state)
            if dry:
                held = ("kill switch is on (.pod/kill-switch)" if os.path.exists(kill) else None) or \
                    branch_stop(name, base, globs, limits)
                if held:
                    print("%s (%s): would stop: %s" % (name, state.risk, held))
                    continue
                actor = "agent:%s" % step.actor if step.actor in ("superbiz", "superdev") else step.actor
                if step.kind == "sign":
                    n = int(step.name.split()[-1])
                    role = agent_sign.next_role(lib.read_log(change_dir), n,
                                                lib.blob_hash(os.path.join(change_dir, lib.ARTIFACTS[n])))
                    actor = "agent:%s" % lib.OWNERS[n][0 if role == "owner" else 1]
                print("%s (%s): next: %s (%s)" % (name, state.risk, step.name, actor))
                continue
            # every check runs before anything of the branch's is used, including the brief at a stop
            stop = "kill switch is on (.pod/kill-switch)" if os.path.exists(kill) else None
            guarded = stop or branch_stop(name, base, globs, limits)
            stop = guarded or (step.name if step.kind == "stop" else None)
            if stop is None:
                at = sponsor.now()
                gate = int(step.name.split()[-1]) if step.kind == "sign" else (3 if "plan" in step.name else 2)
                found = sponsor.stops(sponsor.ledger(lib.ROOT, at, cfg)[0], limits, name, gate, at)
                stop = found[0] if found else None
            if stop is not None:
                needs_escalation = state.risk not in ("low", "medium")  # escalation signs gate 2: brief people
                if not guarded and needs_escalation and stop.startswith("people sign gate 2") and \
                        maybe_brief(change_dir):
                    commit("loop(%s): SuperCEO brief" % name[:3], [change_dir])
                last = last_loop_record(change_dir)
                if not (last and last.get("result") == "stop" and last.get("reason") == stop):
                    record(change_dir, run_id, step.name if step.kind != "stop" else "stop", "stop", stop)
                    commit("loop(%s): stopped" % name[:3], [change_dir])
                print("%s: stopped: %s" % (name, stop))
                stops += 1
                continue
            print("%s: %s (%s)..." % (name, step.name, step.actor), flush=True)
            if step.kind == "draft":
                ok, reason, files = draft(step, change_dir, cfg)
                label = step.name
                if not ok:
                    reason = "%s failed (%s); nothing was committed" % (step.name, reason)
            else:
                ok, outcome, reason = sign(change_dir, int(step.name.split()[-1]))
                label, files = "%s %s" % (step.name, outcome), [change_dir]
            if not ok:
                record(change_dir, run_id, step.name, "refused" if "refused" in reason else "failed", reason)
                commit("loop(%s): stopped" % name[:3], [change_dir])
                print("%s: stopped: %s" % (name, reason))
                stops += 1
                continue
            record(change_dir, run_id, step.name, "ok")
            commit("loop(%s): %s" % (name[:3], step.name), [change_dir] + files)
            print("%s: %s" % (name, label))
            steps += 1
    finally:
        git("checkout", "-q", home)
        if os.path.exists(lock):
            os.remove(lock)
    if not dry:
        print("Loop run: %d steps, %d stops" % (steps, stops))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
