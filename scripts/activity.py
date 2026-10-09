#!/usr/bin/env python3
"""Agent activity log and cost per change (docs/activity-log.md).

    python3 scripts/activity.py hook [--root <dir>]   (reads Claude Code hook JSON on stdin; always exits 0)
    python3 scripts/activity.py summary <change-dir>  (scripts/activity.sh)

activity.log sits next to gates.log in the change folder. One `key=value` record per line:
    event=tool  at session id tool [files] [cmd]                       (PostToolUse)
    event=usage at session agent model input output cache_write cache_write_1h cache_read usd seconds
                                                                       (Stop, SubagentStop, SessionEnd)
Never logged: prompt text, file contents, tool output, and anything after the first word of a command.
"""
import collections
import contextlib
import datetime
import fcntl
import glob
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

LOG = "activity.log"
PRICES = os.path.join("docs", "model-prices")
STALE_DAYS = 90
TOOL_ID_WINDOW = 64 * 1024  # duplicate hooks (both plugins) run at nearly the same time: scan the log tail only
TOKEN_KINDS = ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read")
Price = collections.namedtuple("Price", TOKEN_KINDS)


# ---------- data ----------

def format_record(fields):
    return " ".join("%s=%s" % (k, shlex.quote(str(v))) for k, v in fields.items() if v not in (None, "")) + "\n"


def read_records(path):
    """(records, skipped): records are dicts with an `event`; skipped counts lines not in key=value form."""
    records, skipped = [], 0
    if not os.path.exists(path):
        return records, skipped
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                parts = shlex.split(line)
            except ValueError:
                skipped += 1
                continue
            if not parts or not all("=" in p for p in parts):
                skipped += 1
                continue
            rec = dict(p.split("=", 1) for p in parts)
            if rec.get("event") not in ("tool", "usage"):
                skipped += 1
                continue
            records.append(rec)
    return records, skipped


def read_prices(root):
    """({model: Price}, as_of date or None, problem or None). Malformed lines are ignored."""
    path = os.path.join(root, PRICES)
    prices, as_of = {}, None
    if not os.path.exists(path):
        return prices, None, "%s not found" % PRICES
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line.startswith("as_of:"):
                try:
                    as_of = datetime.date.fromisoformat(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
                continue
            parts = line.split()
            if len(parts) != 1 + len(TOKEN_KINDS):
                continue
            try:
                prices[parts[0]] = Price(*(float(v) for v in parts[1:]))
            except ValueError:
                continue
    return prices, as_of, None


def cost(tokens, price):
    return sum(tokens[k] * getattr(price, k) for k in TOKEN_KINDS) / 1e6


Summary = collections.namedtuple("Summary", "sessions tools files tokens usd unknown seconds first last skipped")


def summarize(records, skipped=0):
    """One pure fold over the records; activity.sh and metrics.sh print from it."""
    sessions, tools, files = set(), collections.Counter(), collections.Counter()
    tokens = collections.defaultdict(lambda: collections.Counter())
    usd, unknown, seconds, stamps = 0.0, set(), 0, []
    for r in records:
        sessions.add(r.get("session", ""))
        if r.get("at"):
            stamps.append(r["at"])
        if r["event"] == "tool":
            tools[r.get("tool", "?")] += 1
            for f in (r.get("files") or "").split(","):
                if f:
                    files[f] += 1
            continue
        model = r.get("model", "?")
        for k in ("input", "output", "cache_write", "cache_read"):
            tokens[model][k] += to_int(r.get(k))
        if r.get("usd") in (None, "", "unknown"):
            unknown.add(model)
        else:
            try:
                usd += float(r["usd"])
            except ValueError:
                unknown.add(model)
        if r.get("agent", "main") == "main":
            seconds += to_int(r.get("seconds"))  # subagents run inside the main turn: wall time counts once
    sessions.discard("")
    return Summary(len(sessions), tools, files, dict(tokens), usd, sorted(unknown), seconds,
                   min(stamps) if stamps else None, max(stamps) if stamps else None, skipped)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ---------- where to write ----------

def branch_change(root):
    """docs/changes/NNN-slug for branch change/NNN-slug when that folder exists, else None."""
    out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root,
                         capture_output=True, text=True, check=False)
    m = re.match(r"^change/(\d{3}-[A-Za-z0-9._-]+)$", out.stdout.strip())
    if not m:
        return None
    path = os.path.join(root, "docs", "changes", m.group(1))
    return path if os.path.isdir(path) else None


def enabled(root):
    return lib.read_pod_yml(root).get("activity_log", "on").lower() not in ("off", "false", "no")


@contextlib.contextmanager
def locked(root):
    folder = os.path.join(root, ".pod", "activity")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, ".lock"), "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield folder
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- PostToolUse ----------

def repo_path(root, path, cwd):
    if not path:
        return None
    full = os.path.realpath(os.path.join(cwd or root, os.path.expanduser(path)))
    real_root = os.path.realpath(root)
    if full != real_root and not full.startswith(real_root + os.sep):
        return "<outside>"
    return os.path.relpath(full, real_root)


def first_word(command):
    """The program a Bash command runs, without leading VAR=value assignments or its directory."""
    try:
        words = shlex.split(command or "")
    except ValueError:
        words = (command or "").split()
    for w in words:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w):
            continue
        return os.path.basename(w)
    return ""


def tool_record(data, root):
    ti = data.get("tool_input") or {}
    files = [repo_path(root, ti.get(k), data.get("cwd")) for k in ("file_path", "notebook_path", "path")]
    files = [f for f in files if f]
    return {"event": "tool", "at": now_iso(), "session": data.get("session_id", ""),
            "id": data.get("tool_use_id", ""), "tool": data.get("tool_name", "?"),
            "files": ",".join(dict.fromkeys(files)),
            "cmd": first_word(ti.get("command")) if data.get("tool_name") == "Bash" else ""}


def already_logged(log, tool_id):
    if not tool_id or not os.path.exists(log):
        return False
    with open(log, "rb") as fh:
        fh.seek(max(0, os.path.getsize(log) - TOOL_ID_WINDOW))
        tail = fh.read().decode("utf-8", "replace")
    return re.search(r"(^|\s)id=%s(\s|$)" % re.escape(shlex.quote(tool_id)), tail, re.M) is not None


# ---------- Stop / SubagentStop ----------

def transcripts(main_path):
    """[(agent, path)]: the session transcript and its subagent transcripts (<session>/subagents/agent-*.jsonl)."""
    found = [("main", main_path)]
    base = main_path[:-len(".jsonl")] if main_path.endswith(".jsonl") else main_path
    for path in sorted(glob.glob(os.path.join(base, "subagents", "agent-*.jsonl"))):
        found.append((os.path.basename(path)[len("agent-"):-len(".jsonl")], path))
    return found


def new_usage(path, cursor):
    """Read complete lines after the cursor. Returns ({model: tokens}, seconds, new cursor).
    Claude Code writes one API response on several lines with the same message id: count each id once."""
    size = os.path.getsize(path)
    offset, seen = cursor.get("offset", 0), cursor.get("seen", [])
    if size < cursor.get("size", 0) or offset > size:
        offset, seen = 0, []  # truncated or replaced transcript: start again
    with open(path, "rb") as fh:
        fh.seek(offset)
        chunk = fh.read()
    end = chunk.rfind(b"\n") + 1
    by_model, stamps, seen_set = {}, [], set(seen)
    for raw in chunk[:end].splitlines():
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if d.get("timestamp") and d.get("type") in ("user", "assistant"):
            stamps.append(d["timestamp"])
        m = d.get("message")
        if d.get("type") != "assistant" or not isinstance(m, dict) or not isinstance(m.get("usage"), dict):
            continue
        if m.get("id") in seen_set:
            continue
        seen_set.add(m.get("id"))
        seen.append(m.get("id"))
        u = m["usage"]
        split = u.get("cache_creation") or {}
        cw1 = to_int(split.get("ephemeral_1h_input_tokens"))
        cw5 = to_int(split.get("ephemeral_5m_input_tokens")) if split else to_int(u.get("cache_creation_input_tokens"))
        t = by_model.setdefault(m.get("model") or "?", collections.Counter())
        t["input"] += to_int(u.get("input_tokens"))
        t["output"] += to_int(u.get("output_tokens"))
        t["cache_write_5m"] += cw5
        t["cache_write_1h"] += cw1
        t["cache_read"] += to_int(u.get("cache_read_input_tokens"))
    seconds = 0
    if len(stamps) > 1:
        seconds = int((lib.parse_iso(max(stamps)) - lib.parse_iso(min(stamps))).total_seconds())
    by_model = {k: v for k, v in by_model.items() if k != "<synthetic>" and any(v.values())}
    return by_model, seconds, {"offset": offset + end, "size": size, "seen": seen[-500:]}


def usage_records(data, root, folder):
    main = data.get("transcript_path") or ""
    if not os.path.exists(main):
        raise OSError("transcript not found (%s)" % (main or "no transcript_path"))
    session = data.get("session_id", "")
    cursor_path = os.path.join(folder, "%s.json" % re.sub(r"[^A-Za-z0-9_.-]", "_", session or "session"))
    cursors = {}
    if os.path.exists(cursor_path):
        with open(cursor_path, encoding="utf-8") as fh:
            cursors = json.load(fh)
    prices, _, _ = read_prices(root)
    records, warnings = [], []
    for agent, path in transcripts(main):
        by_model, seconds, cursors[path] = new_usage(path, cursors.get(path, {}))
        for model, t in sorted(by_model.items()):
            price = prices.get(model)
            if price is None:
                warnings.append("%s has no price in %s, so its cost is unknown. Tokens are still recorded"
                                % (model, PRICES))
            records.append({"event": "usage", "at": now_iso(), "session": session, "agent": agent,
                            "model": model, "input": t["input"], "output": t["output"],
                            "cache_write": t["cache_write_5m"] + t["cache_write_1h"],
                            "cache_write_1h": t["cache_write_1h"], "cache_read": t["cache_read"],
                            "usd": "%.6f" % cost(t, price) if price else "unknown", "seconds": seconds})
            seconds = 0  # the turn's time goes on its first record only
    return records, warnings, cursor_path, cursors


# ---------- commands ----------

def cmd_hook(args):
    try:
        root = args[args.index("--root") + 1] if "--root" in args else None
        data = json.loads(sys.stdin.read() or "{}")
        root = os.path.realpath(root or os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
        if not os.path.isfile(os.path.join(root, "pod.yml")) or not enabled(root):
            return 0
        change = branch_change(root)
        if change is None:
            return 0
        log = os.path.join(change, LOG)
        event = data.get("hook_event_name")
        with locked(root) as folder:
            if event == "PostToolUse":
                rec = tool_record(data, root)
                if already_logged(log, rec["id"]):
                    return 0
                lines, warnings, cursor = [format_record(rec)], [], None
            elif event in ("Stop", "SubagentStop", "SessionEnd"):
                recs, warnings, cursor_path, cursors = usage_records(data, root, folder)
                lines, cursor = [format_record(r) for r in recs], (cursor_path, cursors)
            else:
                return 0
            if lines:
                with open(log, "a", encoding="utf-8") as fh:
                    fh.writelines(lines)
            if cursor:
                with open(cursor[0], "w", encoding="utf-8") as fh:
                    json.dump(cursor[1], fh)
        for w in warnings:
            print(w, file=sys.stderr)
    except Exception as exc:  # never block the agent (R13)
        print("activity log not written: %s. The tool call was not affected" % (exc,), file=sys.stderr)
    return 0


def fmt_tokens(n):
    if n >= 1_000_000:
        return "%.1fM" % (n / 1e6)
    if n >= 1000:
        return "%dk" % round(n / 1000)
    return str(n)


def fmt_cost(s, as_of):
    if not s.unknown:
        return "US$%.2f%s" % (s.usd, " (prices as of %s)" % as_of if as_of else "")
    return "US$%.2f + unknown (%s)" % (s.usd, ", ".join("%s has no price in %s" % (m, PRICES) for m in s.unknown))


def change_totals(change_dir):
    """(time line, cost line) for metrics.sh, or None when there is no activity.log."""
    path = os.path.join(change_dir, LOG)
    if not os.path.exists(path):
        return None
    s = summarize(*read_records(path))
    _, as_of, _ = read_prices(lib.ROOT)
    return lib.fmt_duration(s.seconds), fmt_cost(s, as_of)


def cmd_summary(args):
    if len(args) != 1:
        print("usage: scripts/activity.sh <change-dir>", file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    name = os.path.basename(change_dir.rstrip(os.sep))
    if not os.path.isdir(change_dir):
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    root = lib.ROOT
    if not enabled(root):
        print("Activity log is off in pod.yml (activity_log: off)")
        return 0
    path = os.path.join(change_dir, LOG)
    if not os.path.exists(path):
        print("No agent activity recorded for %s yet (no activity.log). Agents record activity on branch "
              "change/%s in a project with pod.yml." % (name, name))
        return 0
    s = summarize(*read_records(path))
    _, as_of, problem = read_prices(root)
    print("change: %s   Risk: %s" % (name, lib.risk_of(change_dir)))
    print("activity: %s -> %s   sessions: %d" % (s.first or "-", s.last or "-", s.sessions))
    print("tool calls: %d   %s" % (sum(s.tools.values()), ", ".join(
        "%s %d" % (t, n) for t, n in sorted(s.tools.items(), key=lambda x: (-x[1], x[0])))))
    top = sorted(s.files.items(), key=lambda x: (-x[1], x[0]))[:10]
    print("files (top 10): %s" % (", ".join("%s %d" % f for f in top) or "-"))
    for model, t in sorted(s.tokens.items()):
        print("tokens: %s  in %s  out %s  cache write %s  cache read %s" % (
            model, fmt_tokens(t["input"]), fmt_tokens(t["output"]), fmt_tokens(t["cache_write"]),
            fmt_tokens(t["cache_read"])))
    if problem and not s.unknown:
        print("cost: US$%.2f (%s)" % (s.usd, problem))
    else:
        print("cost: %s" % fmt_cost(s, as_of))
    print("agent time: %s" % lib.fmt_duration(s.seconds))
    if s.skipped:
        print("skipped lines: %d (not in key=value form)" % s.skipped)
    if as_of and (datetime.date.today() - as_of).days > STALE_DAYS:
        print("%s is %d days old (as of %s). Check the Anthropic pricing page"
              % (PRICES, (datetime.date.today() - as_of).days, as_of))
    return 0


COMMANDS = {"hook": cmd_hook, "summary": cmd_summary}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
