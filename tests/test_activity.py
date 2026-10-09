"""Tests for change 001: the agent activity log and cost per change (scripts/activity.py, docs/activity-log.md)."""
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

from tests.test_pod_scripts import BIZ, DEV, HOOKS_BIZ, HOOKS_DEV, POD, PodRepo, run

sys.path.insert(0, os.path.join(POD, "scripts"))
import activity  # noqa: E402

OPUS = "claude-opus-5-5"
SECRET = "ghp_SECRETtoken1234567890"


def usage(inp=0, out=0, cw5=0, cw1=0, cr=0):
    return {"input_tokens": inp, "output_tokens": out, "cache_read_input_tokens": cr,
            "cache_creation_input_tokens": cw5 + cw1,
            "cache_creation": {"ephemeral_5m_input_tokens": cw5, "ephemeral_1h_input_tokens": cw1}}


def assistant(msg_id, ts, model=OPUS, **tokens):
    return {"type": "assistant", "timestamp": ts,
            "message": {"id": msg_id, "model": model, "role": "assistant", "usage": usage(**tokens),
                        "content": [{"type": "text", "text": "PROMPT-TEXT-MUST-NOT-BE-LOGGED"}]}}


def user(ts, text="PROMPT-TEXT-MUST-NOT-BE-LOGGED"):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


class ActivityRepo(PodRepo):
    """A pod repo on branch change/001-demo with the price table and a fake Claude Code transcript."""

    def setUp(self):
        super().setUp()
        shutil.copy(os.path.join(POD, "docs", "model-prices"), os.path.join(self.root, "docs", "model-prices"))
        self.change = self.new_change("demo")
        run(["git", "add", "-A"], self.root)
        run(["git", "commit", "-q", "-m", "base"], self.root)
        run(["git", "checkout", "-q", "-b", "change/001-demo"], self.root)
        self.claude = os.path.join(self.root, ".claude-home")
        os.makedirs(self.claude)
        self.transcript = os.path.join(self.claude, "sess-1.jsonl")
        open(self.transcript, "w").close()

    # ---- helpers ----
    def add_lines(self, records, path=None):
        path = path or self.transcript
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")

    def subagent_path(self, agent="abc123"):
        return os.path.join(self.claude, "sess-1", "subagents", "agent-%s.jsonl" % agent)

    def hook(self, event, hooks=HOOKS_DEV, **fields):
        data = {"session_id": "sess-1", "transcript_path": self.transcript, "cwd": self.root,
                "hook_event_name": event}
        data.update(fields)
        return run([os.path.join(hooks, "activity.sh")], self.root,
                   env={"CLAUDE_PROJECT_DIR": self.root}, stdin=json.dumps(data))

    def tool(self, tool_name, tool_input, tool_id="toolu_1", hooks=HOOKS_DEV, response="OUTPUT-MUST-NOT-BE-LOGGED"):
        return self.hook("PostToolUse", hooks=hooks, tool_name=tool_name, tool_input=tool_input,
                         tool_use_id=tool_id, tool_response={"stdout": response})

    def log_path(self):
        return os.path.join(self.change, "activity.log")

    def log_text(self):
        if not os.path.exists(self.log_path()):
            return ""
        with open(self.log_path(), encoding="utf-8") as fh:
            return fh.read()

    def records(self, event=None):
        recs, _ = activity.read_records(self.log_path())
        return [r for r in recs if event is None or r.get("event") == event]


# ---------- R1, R14: which change is active ----------

class ActiveChangeTests(ActivityRepo):
    def test_change_branch_maps_to_folder(self):
        self.assertEqual(activity.branch_change(self.root), self.change)
        self.tool("Read", {"file_path": os.path.join(self.root, "pod.yml")})
        self.assertEqual(len(self.records("tool")), 1)

    def test_other_branch_records_nothing(self):
        run(["git", "checkout", "-q", "-b", "feature/x"], self.root)
        self.assertIsNone(activity.branch_change(self.root))
        res = self.tool("Read", {"file_path": "pod.yml"})
        self.assertEqual(res.returncode, 0)
        self.assertFalse(os.path.exists(self.log_path()))

    def test_branch_without_folder_records_nothing(self):
        run(["git", "checkout", "-q", "-b", "change/009-missing"], self.root)
        self.assertIsNone(activity.branch_change(self.root))

    def test_no_pod_yml_does_nothing(self):
        os.remove(os.path.join(self.root, "pod.yml"))
        res = self.tool("Read", {"file_path": "x"})
        self.assertEqual(res.returncode, 0)
        self.assertFalse(os.path.exists(self.log_path()))

    def test_activity_log_off(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("activity_log: off\n")
        self.tool("Read", {"file_path": "pod.yml"})
        self.assertFalse(os.path.exists(self.log_path()))
        res = self.sh("activity.sh", self.change)
        self.assertIn("Activity log is off in pod.yml (activity_log: off)", res.stdout)


# ---------- R2-R5: tool records ----------

class ToolRecordTests(ActivityRepo):
    def test_fields(self):
        self.tool("Edit", {"file_path": os.path.join(self.root, "app", "x.py"), "old_string": "a", "new_string": "b"})
        r = self.records("tool")[0]
        self.assertEqual(r["session"], "sess-1")
        self.assertEqual(r["tool"], "Edit")
        self.assertEqual(r["id"], "toolu_1")
        self.assertEqual(r["files"], "app/x.py")
        self.assertIn("at", r)

    def test_bash_keeps_first_word_only(self):
        self.tool("Bash", {"command": "GH_TOKEN=%s /usr/local/bin/gh pr create --body 'secret plan'" % SECRET})
        r = self.records("tool")[0]
        self.assertEqual(r["cmd"], "gh")
        text = self.log_text()
        for needle in (SECRET, "secret plan", "GH_TOKEN", "OUTPUT-MUST-NOT-BE-LOGGED", "PROMPT-TEXT"):
            self.assertNotIn(needle, text)

    def test_once_with_both_plugins(self):
        self.tool("Read", {"file_path": "pod.yml"}, hooks=HOOKS_DEV)
        self.tool("Read", {"file_path": "pod.yml"}, hooks=HOOKS_BIZ)
        self.tool("Read", {"file_path": "pod.yml"}, tool_id="toolu_2", hooks=HOOKS_BIZ)
        self.assertEqual([r["id"] for r in self.records("tool")], ["toolu_1", "toolu_2"])

    def test_outside_paths_hidden(self):
        self.tool("Read", {"file_path": os.path.expanduser("~/.ssh/id_rsa")})
        self.tool("Read", {"file_path": os.path.join(self.root, "..", "elsewhere.txt")}, tool_id="toolu_2")
        self.assertEqual([r["files"] for r in self.records("tool")], ["<outside>", "<outside>"])
        self.assertNotIn(".ssh", self.log_text())

    def test_path_with_spaces_round_trips(self):
        self.tool("Write", {"file_path": os.path.join(self.root, "docs", "my notes.md"), "content": "x"})
        self.assertEqual(self.records("tool")[0]["files"], "docs/my notes.md")


# ---------- R6-R9: usage records ----------

class UsageRecordTests(ActivityRepo):
    def turn(self):
        self.add_lines([user("2026-10-09T10:00:00Z"),
                        assistant("msg_1", "2026-10-09T10:00:05Z", inp=10, out=1000, cw1=2000, cr=50000),
                        assistant("msg_1", "2026-10-09T10:00:06Z", inp=10, out=1000, cw1=2000, cr=50000),
                        assistant("msg_2", "2026-10-09T10:01:40Z", inp=5, out=500, cw5=1000, cr=60000)])

    def test_tokens_deduplicated_by_message_id_and_priced(self):
        self.turn()
        self.hook("Stop")
        [r] = self.records("usage")
        self.assertEqual((r["agent"], r["model"]), ("main", OPUS))
        self.assertEqual((int(r["input"]), int(r["output"]), int(r["cache_write"]), int(r["cache_read"])),
                         (15, 1500, 3000, 110000))
        self.assertEqual(int(r["cache_write_1h"]), 2000)
        # Opus 5.5: 4 / 20 / 5 (5m) / 8 (1h) / 0.2 US$ per million tokens
        want = (15 * 4 + 1500 * 20 + 1000 * 5 + 2000 * 8 + 110000 * 0.2) / 1e6
        self.assertAlmostEqual(float(r["usd"]), want, places=6)
        self.assertEqual(int(r["seconds"]), 100)

    def test_incremental_no_double_count(self):
        self.turn()
        self.hook("Stop")
        self.hook("Stop")
        self.assertEqual(len(self.records("usage")), 1)
        self.add_lines([user("2026-10-09T10:05:00Z"), assistant("msg_3", "2026-10-09T10:05:10Z", out=100)])
        self.hook("Stop", hooks=HOOKS_BIZ)
        rs = self.records("usage")
        self.assertEqual([int(r["output"]) for r in rs], [1500, 100])
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".pod", "activity")))

    def test_subagent_transcripts_included(self):
        self.turn()
        self.add_lines([user("2026-10-09T10:00:10Z"),
                        assistant("msg_s1", "2026-10-09T10:00:30Z", model="claude-sonnet-5-5", out=200)],
                       path=self.subagent_path())
        self.hook("SubagentStop")
        self.hook("Stop")
        rs = {(r["agent"], r["model"]): r for r in self.records("usage")}
        self.assertEqual(set(rs), {("main", OPUS), ("abc123", "claude-sonnet-5-5")})
        self.assertAlmostEqual(float(rs[("abc123", "claude-sonnet-5-5")]["usd"]), 200 * 10 / 1e6, places=7)

    def test_unknown_model(self):
        self.add_lines([assistant("msg_x", "2026-10-09T10:00:05Z", model="claude-mystery-9", out=100)])
        res = self.hook("Stop")
        self.assertEqual(res.returncode, 0)
        [r] = self.records("usage")
        self.assertEqual((r["usd"], int(r["output"])), ("unknown", 100))
        self.assertIn("claude-mystery-9 has no price in docs/model-prices", res.stderr)

    def test_truncated_transcript_resets_cursor(self):
        self.turn()
        self.hook("Stop")
        with open(self.transcript, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(assistant("msg_9", "2026-10-09T11:00:00Z", out=7)) + "\n")
        res = self.hook("Stop")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(int(self.records("usage")[-1]["output"]), 7)

    def test_prompt_text_never_logged(self):
        self.turn()
        self.hook("Stop")
        self.assertNotIn("PROMPT-TEXT", self.log_text())


# ---------- R13: failures never block ----------

class FailureTests(ActivityRepo):
    def test_missing_transcript(self):
        os.remove(self.transcript)
        res = self.hook("Stop")
        self.assertEqual(res.returncode, 0)
        self.assertIn("activity log not written", res.stderr)

    def test_unwritable_change_folder(self):
        os.chmod(self.change, 0o500)
        self.addCleanup(os.chmod, self.change, 0o755)
        res = self.tool("Read", {"file_path": "pod.yml"})
        self.assertEqual(res.returncode, 0)
        self.assertIn("The tool call was not affected", res.stderr)

    def test_malformed_price_file(self):
        with open(os.path.join(self.root, "docs", "model-prices"), "w", encoding="utf-8") as fh:
            fh.write("claude-opus-5-5 four twenty\n")
        self.add_lines([assistant("msg_1", "2026-10-09T10:00:05Z", out=10)])
        res = self.hook("Stop")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(self.records("usage")[0]["usd"], "unknown")

    def test_garbage_stdin(self):
        res = run([os.path.join(HOOKS_DEV, "activity.sh")], self.root, env={"CLAUDE_PROJECT_DIR": self.root},
                  stdin="not json")
        self.assertEqual(res.returncode, 0)


# ---------- R11, R12, E1, E2, E6: viewing ----------

class SummaryTests(ActivityRepo):
    def fill(self):
        for i, (tool, inp) in enumerate([("Read", {"file_path": "scripts/lib.py"}),
                                         ("Edit", {"file_path": "scripts/lib.py"}),
                                         ("Bash", {"command": "make check"})]):
            self.tool(tool, inp, tool_id="toolu_%d" % i)
        self.add_lines([user("2026-10-09T10:00:00Z"),
                        assistant("msg_1", "2026-10-09T10:23:00Z", out=1000000)])
        self.hook("Stop")

    def test_summary(self):
        self.fill()
        res = self.sh("activity.sh", self.change)
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout
        self.assertIn("change: 001-demo   Risk: low", out)
        self.assertIn("sessions: 1", out)
        self.assertIn("tool calls: 3   Bash 1, Edit 1, Read 1", out)
        self.assertIn("files (top 10): scripts/lib.py 2", out)
        self.assertIn("tokens: claude-opus-5-5  in 0  out 1.0M  cache write 0  cache read 0", out)
        self.assertIn("cost: US$20.00 (prices as of ", out)
        self.assertIn("agent time: 0h 23m", out)

    def test_empty(self):
        res = self.sh("activity.sh", self.change)
        self.assertEqual(res.returncode, 0)
        self.assertIn("No agent activity recorded for 001-demo yet (no activity.log). Agents record activity "
                      "on branch change/001-demo in a project with pod.yml.", res.stdout)

    def test_missing_folder(self):
        res = self.sh("activity.sh", os.path.join(self.root, "docs", "changes", "999-x"))
        self.assertEqual(res.returncode, 1)
        self.assertIn("change folder not found", res.stderr)

    def test_skipped_lines(self):
        self.fill()
        with open(self.log_path(), "a", encoding="utf-8") as fh:
            fh.write("<<<<<<< HEAD\nnot a record\n")
        res = self.sh("activity.sh", self.change)
        self.assertEqual(res.returncode, 0)
        self.assertIn("skipped lines: 2 (not in key=value form)", res.stdout)

    def test_unknown_cost_in_summary(self):
        self.fill()
        self.add_lines([assistant("msg_x", "2026-10-09T10:30:00Z", model="claude-mystery-9", out=5)])
        self.hook("Stop")
        res = self.sh("activity.sh", self.change)
        self.assertIn("cost: US$20.00 + unknown (claude-mystery-9 has no price in docs/model-prices)", res.stdout)

    def test_stale_prices_warning(self):
        path = os.path.join(self.root, "docs", "model-prices")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join("as_of: 2020-01-01" if l.startswith("as_of:") else l for l in text.splitlines()) + "\n")
        self.fill()
        res = self.sh("activity.sh", self.change)
        self.assertIn("docs/model-prices is", res.stdout)
        self.assertIn("days old (as of 2020-01-01). Check the Anthropic pricing page", res.stdout)

    def test_metrics_lines(self):
        res = self.sh("metrics.sh", self.change)
        self.assertIn("agent time: no activity.log", res.stdout)
        self.assertIn("agent cost: no activity.log", res.stdout)
        self.fill()
        res = self.sh("metrics.sh", self.change)
        self.assertIn("agent time: 0h 23m", res.stdout)
        self.assertIn("agent cost: US$20.00 (prices as of ", res.stdout)


# ---------- R15: committed even with a global *.log ignore ----------

class IgnoreTests(ActivityRepo):
    def test_repo_and_installer_unignore_activity_log(self):
        with open(os.path.join(POD, ".gitignore"), encoding="utf-8") as fh:
            self.assertIn("!docs/changes/*/activity.log", fh.read().splitlines())
        sys.path.insert(0, os.path.join(POD, "scripts"))
        import pod_install
        self.assertIn("!docs/changes/*/activity.log", pod_install.GITIGNORE_LINES)
        self.assertIn("model-prices", pod_install.DOCS)
        self.assertIn("activity-log.md", pod_install.DOCS)

    def test_gate_warns_when_ignored(self):
        with open(os.path.join(self.root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("*.log\n!docs/changes/*/gates.log\n")
        with open(self.log_path(), "w", encoding="utf-8") as fh:
            fh.write("event=tool at=2026-10-09T10:00:00Z session=s id=t tool=Read\n")
        self.as_user(BIZ)
        res = self.sh("gate.sh", self.change, "1")
        self.assertIn("activity.log is ignored by git", res.stdout + res.stderr)


# ---------- R16: fast enough ----------

class SpeedTests(ActivityRepo):
    def test_tool_hook_median_under_100ms_over_baseline(self):
        """The hook's own cost: median wall time minus the bare cost of starting bash + python."""
        base, hook = [], []
        for i in range(20):
            t = time.perf_counter()
            subprocess.run(["bash", "-c", "python3 -c pass"], capture_output=True)
            base.append(time.perf_counter() - t)
            t = time.perf_counter()
            self.tool("Read", {"file_path": "pod.yml"}, tool_id="toolu_%d" % i)
            hook.append(time.perf_counter() - t)
        self.assertLess(statistics.median(hook) - statistics.median(base), 0.100)
