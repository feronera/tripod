#!/usr/bin/env python3
"""Sponsor controls for Autonomous mode: budgets, the risk ceiling, automatic stops and the daily digest
(docs/autonomous.md).

    scripts/digest.sh [--hours N] [--write]        what the agents did and spent in the last N hours
    scripts/resume.sh <change-dir> "<reason>"     a person lets agent checks run again after repeated refusals

Every number comes from the logs that already exist (activity.log, gates.log), read into one ledger, so a
refusal and the digest can never disagree. The limits apply only to agent work (agent-sign and auto-merge).
"""
import collections
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity  # noqa: E402
import lib  # noqa: E402

FLOAT_KEYS = ("budget_per_change_usd", "budget_per_day_usd")
INT_KEYS = ("max_refusals_per_gate", "agent_merges_per_day")
DAY = datetime.timedelta(hours=24)
ESTIMATE_WINDOW = datetime.timedelta(days=7)

Limits = collections.namedtuple("Limits", "per_change per_day max_refusals merges_per_day forbidden")
Event = collections.namedtuple("Event", "at change kind data")


# ---------- limits ----------

def read_limits(cfg):
    """(Limits, problems). A missing key is None (no limit); a malformed or negative one is a problem."""
    values, problems = {}, []
    for key in FLOAT_KEYS + INT_KEYS:
        raw = str(cfg.get(key, "") or "").strip()
        if not raw:
            values[key] = None
            continue
        try:
            value = float(raw) if key in FLOAT_KEYS else int(raw)
        except ValueError:
            problems.append("pod.yml: %s: %s is not a number" % (key, raw))
            values[key] = None
            continue
        if value < 0:
            problems.append("pod.yml: %s: %s must not be negative" % (key, raw))
            values[key] = None
            continue
        values[key] = value
    forbidden = tuple(lib.split_list(cfg.get("agent_forbidden_paths", "")))
    return Limits(values["budget_per_change_usd"], values["budget_per_day_usd"], values["max_refusals_per_gate"],
                  values["agent_merges_per_day"], forbidden), problems


def limits_text(limits):
    parts = []
    for name, value, fmt in (("budget_per_change_usd", limits.per_change, "%.2f"),
                             ("budget_per_day_usd", limits.per_day, "%.2f"),
                             ("max_refusals_per_gate", limits.max_refusals, "%d"),
                             ("agent_merges_per_day", limits.merges_per_day, "%d")):
        if value is not None:
            parts.append("%s %s" % (name, fmt % value))
    if limits.forbidden:
        parts.append("agent_forbidden_paths %s" % ", ".join(limits.forbidden))
    return ", ".join(parts) or "none set"


def forbidden_files(files, limits):
    return [f for f in files if any(lib.path_matches(f, g) for g in limits.forbidden)]


# ---------- the ledger ----------

def now():
    """The current time in UTC; TRIPOD_NOW (ISO 8601) fixes it for tests and demos."""
    fixed = os.environ.get("TRIPOD_NOW")
    if fixed:
        return lib.parse_iso(fixed).astimezone(datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)


def parse_at(value):
    try:
        at = lib.parse_iso(value or "")
    except ValueError:
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=datetime.timezone.utc)
    return at.astimezone(datetime.timezone.utc)


def ledger(root=lib.ROOT, until=None):
    """(events, skipped) from every change's activity.log and gates.log, oldest first. Events after `until`
    (the current time) are left out, so the ledger is read as of now."""
    until = until or now()
    events, skipped = [], 0
    for change_dir in lib.change_dirs(root):
        change = os.path.basename(change_dir)
        records, _ = activity.read_records(os.path.join(change_dir, activity.LOG))
        rows = [(r, {"usage": "usage", "verdict": "verdict"}.get(r.get("event"))) for r in records]
        for e in lib.read_log(change_dir):
            if e.get("event") in ("revert", "resume"):
                rows.append((e, e["event"]))
            elif e.get("role") == "auto" and e["gate"] == 4:
                rows.append((e, "auto"))
            elif 1 <= e["gate"] <= 4 and e.get("role") in ("owner", "cross", "escalation"):
                rows.append((e, "signature"))
        for data, kind in rows:
            if not kind:
                continue
            at = parse_at(data.get("at"))
            if at is None:
                skipped += 1
                continue
            if at <= until:
                events.append(Event(at, change, kind, data))
    events.sort(key=lambda e: e.at)
    return events, skipped


def usd_of(event):
    try:
        return float(event.data.get("usd", "")), True
    except ValueError:
        return 0.0, False


def spend(events, change=None, since=None):
    """(usd, unknown records) of usage events, for one change or all, since a time or ever."""
    total, unknown = 0.0, 0
    for e in events:
        if e.kind != "usage" or (change and e.change != change) or (since and e.at <= since):
            continue
        usd, known = usd_of(e)
        total += usd
        unknown += 0 if known else 1
    return total, unknown


def estimate(events, at):
    """The most expensive agent-sign run (usage summed per session) in the last 7 days."""
    runs = collections.Counter()
    for e in events:
        if e.kind == "usage" and e.data.get("source") == "agent-sign" and e.at > at - ESTIMATE_WINDOW:
            runs[(e.change, e.data.get("session"))] += usd_of(e)[0]
    return max(runs.values(), default=0.0)


def person_acted(events, change):
    """The last time a person signed a gate of the change or ran resume.sh, or None."""
    times = [e.at for e in events if e.change == change and (
        e.kind == "resume" or (e.kind == "signature" and not lib.is_agent(e.data)))]
    return max(times, default=None)


def refusals(events, change, gate):
    since = person_acted(events, change)
    return sum(1 for e in events if e.change == change and e.kind == "verdict" and str(e.data.get("gate")) == str(gate)
               and e.data.get("verdict") != "approve" and (since is None or e.at > since))


def recent_revert(events, at):
    reverts = [e for e in events if e.kind == "revert" and e.at > at - DAY]
    return reverts[-1] if reverts else None


def fmt_time(at):
    return at.strftime("%Y-%m-%d %H:%M")


def stops(events, limits, change, gate, at):
    """Reasons agent-sign must not start an agent for this change and gate (empty = go)."""
    reasons = []
    guess = estimate(events, at)
    if limits.per_change is not None:
        spent, _ = spend(events, change)
        if spent + guess > limits.per_change + 1e-9:
            reasons.append("budget for %s reached: spent US$%.2f of US$%.2f (budget_per_change_usd), and the next "
                           "check may cost about US$%.2f. The sponsor can raise the limit in pod.yml"
                           % (change, spent, limits.per_change, guess))
    if limits.per_day is not None:
        spent, _ = spend(events, since=at - DAY)
        if spent + guess > limits.per_day + 1e-9:
            reasons.append("today's budget reached: spent US$%.2f in the last 24 hours of US$%.2f "
                           "(budget_per_day_usd), next check about US$%.2f. The sponsor can raise the limit in pod.yml"
                           % (spent, limits.per_day, guess))
    if limits.max_refusals is not None:
        count = refusals(events, change, gate)
        if count >= limits.max_refusals:
            reasons.append("gate %s has %d refused agent checks since a person last acted (max_refusals_per_gate: %d). "
                           "A person reviews it, then runs scripts/resume.sh docs/changes/%s \"<reason>\""
                           % (gate, count, limits.max_refusals, change))
    revert = recent_revert(events, at)
    if revert:
        reasons.append("%s was reverted at %s UTC; agents pause for 24 hours after a revert (until %s UTC)"
                       % (revert.change, fmt_time(revert.at), fmt_time(revert.at + DAY)))
    return reasons


def merges_today(events, at):
    return sum(1 for e in events if e.kind == "auto" and e.at > at - DAY)


def budget_warnings(events, limits, change, at):
    """[(which, spent, limit)] for budgets already reached (no estimate): the hook's warning."""
    out = []
    if limits.per_change is not None:
        spent, _ = spend(events, change)
        if spent >= limits.per_change:
            out.append(("change", spent, limits.per_change))
    if limits.per_day is not None:
        spent, _ = spend(events, since=at - DAY)
        if spent >= limits.per_day:
            out.append(("day", spent, limits.per_day))
    return out


def hook_warning(root, change_dir, session):
    """JSON for a PostToolUse hook when a budget is reached, once per session per limit; else None."""
    cfg = lib.read_pod_yml(root)
    limits, problems = read_limits(cfg)
    if problems or (limits.per_change is None and limits.per_day is None):
        return None
    at = now()
    events, _ = ledger(root, at)
    warnings = budget_warnings(events, limits, os.path.basename(change_dir), at)
    folder = os.path.join(root, ".pod", "activity")
    os.makedirs(folder, exist_ok=True)
    texts = []
    for which, spent, limit in warnings:
        marker = os.path.join(folder, "%s.warned-%s" % ("".join(c if c.isalnum() or c in "-_." else "_"
                                                                 for c in session or "session"), which))
        if os.path.exists(marker):
            continue
        open(marker, "w").close()
        texts.append("Tripod: the %s budget is reached (US$%.2f of US$%.2f). scripts/agent-sign.sh will refuse until "
                     "the sponsor raises it. Finish the current step and hand over" % (which, spent, limit))
    if not texts:
        return None
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(texts)}})


# ---------- digest ----------

def digest(events, skipped, limits, at, hours):
    since = at - datetime.timedelta(hours=hours)
    window = [e for e in events if e.at > since]
    nothing = "nothing in the last %d hours" % hours
    lines = ["Tripod digest, last %d hours (%s → %s UTC)" % (hours, fmt_time(since), fmt_time(at))]
    total, unknown = spend(window)
    limit = " (limit US$%.2f per day)" % limits.per_day if limits.per_day is not None and hours == 24 else ""
    lines.append("spend: US$%.2f%s · unknown: %d records" % (total, limit, unknown))
    by_change = collections.OrderedDict()
    for e in window:
        if e.kind == "usage":
            usd, known = usd_of(e)
            if known:
                by_change.setdefault(e.change, collections.Counter())[e.data.get("model", "?")] += usd
    for change, models in sorted(by_change.items()):
        lines.append("  %s US$%.2f (%s)" % (change, sum(models.values()), ", ".join(
            "%s US$%.2f" % (m, v) for m, v in sorted(models.items()))))

    def section(title, items):
        lines.append("%s: %s" % (title, "; ".join(items) if items else nothing))

    signed = collections.OrderedDict()
    for e in window:
        if e.kind == "signature" and lib.is_agent(e.data):
            signed.setdefault(e.change, []).append("gate %d %s %s" % (e.data["gate"], e.data.get("role"),
                                                                      e.data.get("model", "?")))
    section("agent signatures", ["%s %s" % (c, ", ".join(v)) for c, v in signed.items()])
    refused = collections.OrderedDict()
    for e in window:
        if e.kind == "verdict" and e.data.get("verdict") != "approve":
            refused.setdefault(e.change, collections.Counter())[e.data.get("gate", "?")] += 1
    section("refused agent checks", ["%s %d (%s)" % (c, sum(g.values()), ", ".join(
        "gate %s: %d" % (k, v) for k, v in sorted(g.items()))) for c, g in refused.items()])
    section("auto-merges", ["%s at %s" % (e.change, fmt_time(e.at)) for e in window if e.kind == "auto"])
    section("reverts", ["%s at %s by %s: %s" % (e.change, fmt_time(e.at), e.data.get("by", "-"), e.data.get("reason", "-"))
                        for e in window if e.kind == "revert"])
    section("resumes", ["%s at %s by %s: %s" % (e.change, fmt_time(e.at), e.data.get("by", "-"), e.data.get("reason", "-"))
                        for e in window if e.kind == "resume"])
    in_force = []
    revert = recent_revert(events, at)
    if revert:
        in_force.append("%s reverted at %s UTC; agents pause until %s UTC"
                        % (revert.change, fmt_time(revert.at), fmt_time(revert.at + DAY)))
    if limits.max_refusals is not None:
        for change, gates in refused.items():
            for gate in sorted(gates):
                count = refusals(events, change, gate)
                if count >= limits.max_refusals:
                    in_force.append("%s gate %s: %d refusals in a row (max_refusals_per_gate: %d); resume with "
                                    "scripts/resume.sh" % (change, gate, count, limits.max_refusals))
    if limits.per_change is not None:
        for change in sorted({e.change for e in events if e.kind == "usage"}):
            total, _ = spend(events, change)
            if total >= limits.per_change:
                in_force.append("%s budget reached (US$%.2f of US$%.2f, budget_per_change_usd)"
                                % (change, total, limits.per_change))
    if limits.per_day is not None:
        day, _ = spend(events, since=at - DAY)
        if day >= limits.per_day:
            in_force.append("today's budget reached (US$%.2f of US$%.2f)" % (day, limits.per_day))
    section("stops in force", in_force)
    lines.append("limits: " + limits_text(limits))
    if skipped:
        lines.append("skipped records: %d (no readable time)" % skipped)
    return "\n".join(lines) + "\n"


# ---------- commands ----------

def cmd_digest(args):
    hours, write = 24, False
    i = 0
    while i < len(args):
        if args[i] == "--hours" and i + 1 < len(args) and args[i + 1].isdigit() and int(args[i + 1]) > 0:
            hours, i = int(args[i + 1]), i + 2
        elif args[i] == "--write":
            write, i = True, i + 1
        else:
            print("usage: scripts/digest.sh [--hours N] [--write]", file=sys.stderr)
            return 2
    limits, problems = read_limits(lib.read_pod_yml())
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    at = now()
    events, skipped = ledger(lib.ROOT, at)
    text = digest(events, skipped, limits, at, hours)
    print(text, end="")
    if write:
        folder = os.path.join(lib.ROOT, "docs", "digest")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, at.strftime("%Y-%m-%d") + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("```\n" + text + "```\n")
        print("Wrote %s" % os.path.relpath(path, lib.ROOT))
    return 0


def cmd_resume(args):
    if len(args) != 2 or not args[1].strip():
        print('usage: scripts/resume.sh <change-dir> "<reason>"', file=sys.stderr)
        return 2
    change_dir = os.path.abspath(args[0])
    if not os.path.isdir(change_dir):
        print("change folder not found: %s" % args[0], file=sys.stderr)
        return 1
    cfg = lib.read_pod_yml()
    email = lib.git_email()
    allowed = {e for r in ("superbiz", "superdev", "escalation") for e in lib.role_emails(cfg, r)}
    allowed.update(lib.split_list(cfg.get("sponsor_email", "").lower()))
    if not email or email not in allowed:
        print("Refused: git email '%s' is not the sponsor or a member in pod.yml" % (email or "-"))
        return 1
    reason = " ".join(args[1].replace('"', "'").split())
    with open(os.path.join(change_dir, "gates.log"), "a", encoding="utf-8") as fh:
        fh.write('event=resume by=%s at=%s reason="%s"\n' % (email, now().isoformat(timespec="seconds"), reason))
    print("Resumed: %s (agent checks may run again on every gate)" % os.path.basename(change_dir))
    return 0


COMMANDS = {"digest": cmd_digest, "resume": cmd_resume}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
