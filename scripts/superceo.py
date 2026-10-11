#!/usr/bin/env python3
"""The SuperCEO agent: ranks the work and prepares decisions for people. It signs nothing.

    scripts/superceo.sh priorities          docs/superceo/YYYY-MM-DD.md: open changes and backlog, ranked
    scripts/superceo.sh brief <change-dir>  docs/changes/NNN-slug/brief.md for a medium or high change at a gate

The agent runs read-only (`--tools Read,Grep,Glob`); this script writes the files from its answer.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity  # noqa: E402
import lib  # noqa: E402
import sponsor  # noqa: E402

READ_ONLY = "Read,Grep,Glob"


def run_ceo(prompt, cfg):
    model = cfg.get("superceo_model") or cfg.get("superbiz_agent_model") or ""
    cmd = [os.environ.get("TRIPOD_CLAUDE", "claude"), "-p", prompt, "--output-format", "json",
           "--tools", READ_ONLY, "--allowedTools", READ_ONLY]
    if model:
        cmd += ["--model", model]
    folder = None
    for base in (os.environ.get("TRIPOD_PLUGIN_DIR"), os.path.join(lib.ROOT, "plugins")):
        if base and os.path.isdir(os.path.join(base, "superceo")):
            folder = os.path.join(base, "superceo")
            break
    if folder:
        cmd += ["--plugin-dir", folder]
    try:
        out = subprocess.run(cmd, cwd=lib.ROOT, capture_output=True, text=True, timeout=cfg["agent_sign_timeout"],
                             stdin=subprocess.DEVNULL, check=False)
    except FileNotFoundError:
        return None, "claude is not installed"
    except subprocess.TimeoutExpired:
        return None, "no answer within %d s" % cfg["agent_sign_timeout"]
    if out.returncode != 0:
        return None, "claude exited %d" % out.returncode
    try:
        import json
        data = json.loads(out.stdout)
    except ValueError:
        return None, "the output was not JSON"
    return data, None


def change_summary(cfg):
    """One line per change folder in the working tree: Risk, gates passed, spend."""
    at = sponsor.now()
    events, _ = sponsor.ledger(lib.ROOT, at, cfg)
    lines = []
    for change_dir in lib.change_dirs():
        name = os.path.basename(change_dir)
        risk = lib.risk_of(change_dir)
        passed = 0
        for n in (1, 2, 3, 4):
            if lib.check_gate(change_dir, n, cfg, None, risk, release=(n == 4)):
                break
            passed = n
        spent, _ = sponsor.spend(events, name)
        lines.append("- %s: Risk %s, passed gate %d, spend US$%.2f" % (name, risk, passed, spent))
    return lines


def cmd_priorities(cfg):
    lines = change_summary(cfg)
    backlog = os.path.join(lib.ROOT, "docs", "backlog.md")
    if not lines and not os.path.exists(backlog):
        print("No open changes and no docs/backlog.md: nothing to rank")
        return 0
    prompt = "\n".join([
        "Use the priorities skill (/superceo:priorities). Rank the open changes and the backlog for the sponsor.",
        "Changes (from gates.log and activity.log):", *lines,
        "Backlog: docs/backlog.md" if os.path.exists(backlog) else "Backlog: none",
        "Read docs/changes/*/intent.md and the latest digest (scripts/digest.sh output is not available; read the "
        "logs) as needed. Answer in Markdown: a numbered list, one change or backlog item per line, each with its "
        "state, next step, blocker, spend and a one-line reason for its rank.",
    ])
    print("Ranking with %s..." % (cfg.get("superceo_model") or "the default model"), flush=True)
    data, error = run_ceo(prompt, cfg)
    if data is None:
        print("superceo: claude did not return a ranking (%s). Nothing was written" % error)
        return 1
    folder = os.path.join(lib.ROOT, "docs", "superceo")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, sponsor.now().strftime("%Y-%m-%d") + ".md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Priorities, %s UTC (SuperCEO, %s)\n\n%s\n" % (
            sponsor.fmt_time(sponsor.now()), cfg.get("superceo_model") or "-", (data.get("result") or "").strip()))
    print("Wrote %s" % os.path.relpath(path, lib.ROOT))
    return 0


def cmd_brief(change_dir, cfg):
    name = os.path.basename(change_dir)
    risk = lib.risk_of(change_dir)
    if risk == "low":
        print("Refused: %s is Risk: low; briefs are for decisions people make" % name)
        return 1
    entries = lib.read_log(change_dir)
    gate = next((n for n in (1, 2, 3, 4) if lib.check_gate(change_dir, n, cfg, entries, risk, release=(n == 4))), None)
    if gate is None:
        print("Refused: %s has passed every gate; there is no decision waiting" % name)
        return 1
    artifact = os.path.join(change_dir, lib.ARTIFACTS[gate])
    blob = lib.blob_hash(artifact) if os.path.exists(artifact) else "-"
    rel = os.path.relpath(change_dir, lib.ROOT)
    prompt = "\n".join([
        "Use the brief skill (/superceo:brief). %s (Risk: %s) is waiting for people at gate %d (%s)." % (
            rel, risk, gate, lib.ARTIFACTS[gate]),
        "Read the change's artifacts, gates.log and activity.log. Write the brief in Markdown with these sections: "
        "## Decision, ## Options, ## Risks, ## Evidence (links to files), ## Recommendation. Do not sign anything.",
    ])
    print("Writing a brief for %s (gate %d, Risk: %s)..." % (name, gate, risk), flush=True)
    data, error = run_ceo(prompt, cfg)
    if data is None:
        print("superceo: claude did not return a brief (%s). Nothing was written" % error)
        return 1
    with open(os.path.join(change_dir, "brief.md"), "w", encoding="utf-8") as fh:
        fh.write("# Brief: %s, gate %d\n\nartifact_blob: %s\nwritten: %s UTC by SuperCEO (%s)\n\n%s\n" % (
            name, gate, blob, sponsor.fmt_time(sponsor.now()), cfg.get("superceo_model") or "-",
            (data.get("result") or "").strip()))
    print("Wrote %s" % os.path.join(rel, "brief.md"))
    return 0


def main(args):
    cfg = lib.read_pod_yml()
    if args == ["priorities"]:
        return cmd_priorities(cfg)
    if len(args) == 2 and args[0] == "brief":
        change_dir = os.path.abspath(args[1])
        if not os.path.isdir(change_dir) or os.path.dirname(os.path.realpath(change_dir)) != os.path.realpath(
                lib.CHANGES_DIR):
            print("change folder not found in docs/changes: %s" % args[1], file=sys.stderr)
            return 1
        return cmd_brief(change_dir, cfg)
    print("usage: scripts/superceo.sh priorities | brief <change-dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
