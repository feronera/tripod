#!/usr/bin/env python3
"""Sign one seat of a gate as an agent, in Autonomous mode (docs/autonomous.md).

    scripts/agent-sign.sh <change-dir> <gate>

Starts `claude -p` on the model of the seat the gate needs next (owner first, then cross), with read-only tools,
and records its APPROVE in gates.log as `by=agent:<leg> model=<model> session=<id>`. People sign with
scripts/gate.sh instead; gate 1 and any change that is not Risk: low always need people.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity  # noqa: E402
import lib  # noqa: E402
import sponsor  # noqa: E402

READ_ONLY_TOOLS = "Read,Grep,Glob"
INPUTS = {2: ("intent.md", "ux-brief.md", "spec.md"), 3: ("intent.md", "spec.md", "plan.md"),
          4: ("spec.md", "plan.md", "review.md", "acceptance.md")}
VERDICT = re.compile(r"^\s*`?VERDICT:\s*(APPROVE|REFUSE)`?\s*$")



def refuse(message):
    print("Refused: " + message)
    return 1


def gate_questions(gate):
    """The `### Gate N` section of docs/gates.md, or a short fallback."""
    path = os.path.join(lib.ROOT, "docs", "gates.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        m = re.search(r"^### Gate %d:.*?(?=^### |^## |\Z)" % gate, text, re.M | re.S)
        if m:
            return m.group(0).strip()
    return "### Gate %d\n- Is %s complete, consistent with the earlier artifacts, and testable?" % (
        gate, lib.ARTIFACTS[gate])


def prompt(change_dir, gate, role, leg):
    rel = os.path.relpath(change_dir, lib.ROOT)
    files = [os.path.join(rel, f) for f in INPUTS[gate] if os.path.exists(os.path.join(change_dir, f))]
    duty = ("You are the %s agent and you own gate %d: you are accountable for %s."
            % (lib.LABEL[leg], gate, lib.ARTIFACTS[gate]) if role == "owner" else
            "You are the %s agent and you cross-check gate %d. The other leg wrote %s; your job is to find what "
            "it missed. Do not trust it." % (lib.LABEL[leg], gate, lib.ARTIFACTS[gate]))
    return "\n".join([
        duty,
        "Read these files (read-only; do not change anything): " + ", ".join(files),
        "Answer every question below with yes or no and one line of evidence that cites a file and a requirement "
        "or line. Refuse if any answer is no, if a requirement of an earlier artifact is missing from a later one, "
        "or if you are unsure.",
        "",
        gate_questions(gate),
        "",
        "Quote nothing from files outside the change's artifacts and the code they name; never quote secrets.",
        "End with exactly one line: `VERDICT: APPROVE` or `VERDICT: REFUSE`.",
    ])


def read_verdict(result):
    """APPROVE only when the last non-empty line is `VERDICT: APPROVE` and it is the only VERDICT line.
    Anything else is REFUSE, so text quoted from an artifact cannot decide the verdict."""
    lines = [l for l in (result or "").splitlines() if l.strip()]
    found = [l for l in lines if VERDICT.match(l)]
    if not lines or len(found) != 1 or found[0] is not lines[-1]:
        return "REFUSE", len(found)
    return VERDICT.match(lines[-1]).group(1), 1


def changed_files(cfg):
    """Files this branch changes against the base branch, including edits not committed yet and new files,
    so an edit cannot hide until after the signature."""
    base = lib.resolve_base(cfg["base_branch"])
    rc, merge_base, _ = lib.git_out(["merge-base", "HEAD", base], lib.ROOT)
    files = set()
    # --no-renames: a file moved out of a forbidden or risky path shows both its old and its new path
    for args in (["diff", "--no-renames", "--name-only", merge_base] if rc == 0 and merge_base
                 else ["diff", "--no-renames", "--name-only", "HEAD"],
                 ["ls-files", "--others", "--exclude-standard"]):
        rc2, out, _ = lib.git_out(args, lib.ROOT)
        if rc2 == 0:
            files.update(f for f in out.splitlines() if f)
    return sorted(files)


def next_role(entries, gate, blob):
    """The seat that signs next, judged like gate-check (the latest signature per role): owner until it is
    current, then cross; None when both are current."""
    latest = {}
    for e in entries:
        if e["gate"] == gate and e.get("role") in ("owner", "cross"):
            latest[e["role"]] = e
    for role in ("owner", "cross"):
        if role not in latest or latest[role].get("blob") != blob:
            return role
    return None


def run_claude(text, model, timeout):
    cmd = [os.environ.get("TRIPOD_CLAUDE", "claude"), "-p", text, "--model", model,
           "--output-format", "json",
           # --tools limits which tools exist (--allowedTools alone only adds permissions to the user's settings);
           # --safe-mode and --strict-mcp-config keep the repo's CLAUDE.md, hooks, plugins and MCP servers out
           "--tools", READ_ONLY_TOOLS, "--allowedTools", READ_ONLY_TOOLS, "--safe-mode", "--strict-mcp-config"]
    try:
        out = subprocess.run(cmd, cwd=lib.ROOT, capture_output=True, text=True, timeout=timeout, check=False,
                             stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return None, "claude is not installed (set TRIPOD_CLAUDE or install Claude Code)"
    except subprocess.TimeoutExpired:
        return None, "no answer within %d s (agent_sign_timeout)" % timeout
    if out.returncode != 0:
        return None, "claude exited %d: %s" % (out.returncode, (out.stderr or out.stdout).strip()[:200])
    try:
        return json.loads(out.stdout), None
    except ValueError:
        return None, "the output was not JSON"


def write_evidence(change_dir, data):
    """Usage for the checking session, one record per model, from Claude Code's own numbers. Written for every
    run (approved or refused) so the sponsor sees the cost, unless the plugin hooks already wrote it."""
    path = os.path.join(change_dir, activity.LOG)
    session = data.get("session_id", "")
    records, _ = activity.read_records(path)
    if any(r.get("event") == "usage" and r.get("session") == session for r in records):
        return
    lines, seconds = [], int((data.get("duration_ms") or 0) / 1000)
    for model, u in sorted((data.get("modelUsage") or {}).items()):
        lines.append(activity.format_record({
            "event": "usage", "at": activity.now_iso(), "session": session, "agent": "main", "model": model,
            "input": u.get("inputTokens", 0), "output": u.get("outputTokens", 0),
            "cache_write": u.get("cacheCreationInputTokens", 0), "cache_write_1h": 0,
            "cache_read": u.get("cacheReadInputTokens", 0), "usd": "%.6f" % float(u.get("costUSD", 0) or 0),
            "seconds": seconds, "source": "agent-sign"}))
        seconds = 0
    with open(path, "a", encoding="utf-8") as fh:
        fh.writelines(lines)


def record_verdict(change_dir, session, gate, role, by, model, verdict):
    """`event=verdict` in activity.log. A refused run can never back a signature (gate-check reads it)."""
    with open(os.path.join(change_dir, activity.LOG), "a", encoding="utf-8") as fh:
        fh.write(activity.format_record({"event": "verdict", "at": activity.now_iso(), "run": session,
                                         "gate": gate, "role": role, "by": by, "model": model,
                                         "verdict": verdict.lower()}))


def main(args):
    if len(args) != 2 or args[1] not in ("1", "2", "3", "4"):
        print("usage: scripts/agent-sign.sh <change-dir> <2|3|4>", file=sys.stderr)
        return 2
    change_dir, gate = os.path.abspath(args[0]), int(args[1])
    if not os.path.isdir(change_dir):
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    cfg = lib.read_pod_yml()
    if os.path.exists(os.path.join(lib.ROOT, ".pod", "kill-switch")):
        return refuse("kill switch is on (.pod/kill-switch). No agent was started")
    if cfg["mode"] != "autonomous":
        return refuse("pod.yml sets mode: %s. Agents may sign only in mode: autonomous" % cfg["mode"])
    errors, _ = lib.pod_config_problems(cfg)
    limits, limit_problems = sponsor.read_limits(cfg)
    errors += limit_problems
    if errors:
        return refuse("pod.yml has problems, so no agent was started:\n  - " + "\n  - ".join(errors))
    if gate == 1:
        return refuse("gate 1 is always signed by people, who decide the risk")
    risk = lib.risk_of(change_dir)
    if risk != "low":
        return refuse("Risk is %s. Agents may sign only Risk: low changes; medium and high need people" % risk)
    artifact = os.path.join(change_dir, lib.ARTIFACTS[gate])
    if not os.path.exists(artifact):
        return refuse("%s not found in %s. The artifact must exist before gate %d is signed"
                      % (lib.ARTIFACTS[gate], args[0], gate))
    before = lib.check_change(change_dir, cfg, gate - 1)
    if before:
        return refuse("gate %d must be complete first\n  - %s" % (gate - 1, "\n  - ".join(before)))
    if gate == 3:
        plan_problems = lib.check_plan(artifact, cfg)
        if plan_problems:
            return refuse("plan.md does not follow the required structure\n  - " + "\n  - ".join(plan_problems))
    if lib.log_ignored(change_dir):
        return refuse(lib.IGNORED_HINT)
    if lib.log_ignored(change_dir, "activity.log"):
        print("Warning: " + lib.ACTIVITY_IGNORED_HINT + ". The evidence for agent signatures lives there, "
              "so gate-check in CI will reject them")
    files = changed_files(cfg)
    risky = lib.risky_files(files, lib.ROOT)
    if risky:
        return refuse("this change touches a sensitive path (%s), so its effective risk is high and people sign it"
                      % ", ".join(risky))
    steering = lib.governance_files(files)
    if steering:
        return refuse("this change edits agent instructions (%s), which could steer its own checker, so people "
                      "sign it" % ", ".join(steering))
    banned = sponsor.forbidden_files(files, limits)
    if banned:
        return refuse("this change touches %s, which agents may not change (agent_forbidden_paths); people sign it"
                      % ", ".join(banned))
    entries = lib.read_log(change_dir)
    if gate == 4 and not lib.auto_entry(entries):
        return refuse("agents sign gate 4 only after an auto-merge (no role=auto record in gates.log)")
    blob = lib.blob_hash(artifact)
    role = next_role(entries, gate, blob)
    if role is None:
        return refuse("gate %d is already complete for the current %s" % (gate, lib.ARTIFACTS[gate]))
    at = sponsor.now()
    events, _ = sponsor.ledger(lib.ROOT, at)
    stopped = sponsor.stops(events, limits, os.path.basename(change_dir), gate, at)
    if stopped:
        return refuse(stopped[0] if len(stopped) == 1 else "the sponsor's limits stop agent checks here:\n  - "
                      + "\n  - ".join(stopped))
    leg = lib.OWNERS[gate][0 if role == "owner" else 1]
    model = cfg["%s_agent_model" % leg]
    by = lib.AGENT_PREFIX + leg
    print("Checking gate %d as %s (%s, %s)..." % (gate, role, by, model), flush=True)

    data, error = run_claude(prompt(change_dir, gate, role, leg), model, cfg["agent_sign_timeout"])
    if data is None:
        print("agent-sign: claude did not return a verdict (%s). Nothing was recorded" % error)
        return 1
    session = data.get("session_id", "")
    if not session:
        print("agent-sign: claude did not return a session id, so the check cannot be traced. Nothing was recorded")
        return 1
    write_evidence(change_dir, data)
    used = set((data.get("modelUsage") or {}).keys())
    if model not in used:
        print("agent-sign: the agent ran on %s, not on %s as pod.yml sets for %s. Nothing was recorded"
              % (", ".join(sorted(used)) or "an unknown model", model, by))
        return 1
    result = data.get("result") or ""
    verdict, count = read_verdict(result)
    record_verdict(change_dir, session, gate, role, by, model, verdict)
    if verdict != "APPROVE":
        reasons = "\n".join(l for l in result.splitlines() if not VERDICT.match(l)).strip() or "(no reasons given)"
        note = "" if count == 1 else ("no single VERDICT line at the end (found %d), so it counts as REFUSE. " % count)
        print("REFUSE gate %d %s (%s, %s): %s%s" % (gate, role, by, model, note, reasons))
        return 1

    lines = []
    if not any(e.get("event") == "mode" for e in entries):
        lines.append("event=mode mode=autonomous superbiz_agent_model=%s superdev_agent_model=%s at=%s\n"
                     % (cfg["superbiz_agent_model"], cfg["superdev_agent_model"], lib.now_iso()))
    lines.append("gate=%d role=%s by=%s model=%s session=%s at=%s blob=%s\n"
                 % (gate, role, by, model, session, lib.now_iso(), blob))
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.writelines(lines)
    print("APPROVE gate %d %s (%s, %s)" % (gate, role, by, model))
    print("Recorded: " + lines[-1].strip())
    missing = lib.check_gate(change_dir, gate, cfg, release=True)
    if missing:
        print("gate %d is not complete%s:" % (gate, " for release" if gate == 4 else ""))
        for p in missing:
            print("  - " + p)
    else:
        print("gate %d is complete" % gate)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
