"""Tests added at review for change 001 (approved by the PO while tests/test_activity.py stays locked).
They cover the review findings: SessionEnd, branch switches (E3), missing transcripts (E5), a missing price
table (E6), log injection, MCP tool paths, idle time, and the hook registration."""
import json
import os

from tests.test_activity import (HOOKS_BIZ, HOOKS_DEV, OPUS, ActivityRepo, activity, assistant, run, user)


def tool_result(ts):
    return {"type": "user", "timestamp": ts,
            "message": {"role": "user", "content": [{"type": "tool_result", "content": "OUTPUT"}]}}


class SessionEndTests(ActivityRepo):
    def test_session_end_picks_up_the_last_response(self):
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=100)])
        self.hook("Stop")
        # Claude Code writes the final response after the Stop hook has run
        self.add_lines([assistant("msg_2", "2026-10-09T10:00:09Z", out=40)])
        self.hook("SessionEnd")
        self.assertEqual([int(r["output"]) for r in self.records("usage")], [100, 40])

    def test_session_end_after_stop_adds_nothing(self):
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=100)])
        self.hook("Stop")
        self.hook("SessionEnd", hooks=HOOKS_BIZ)
        self.assertEqual(len(self.records("usage")), 1)


class BranchSwitchTests(ActivityRepo):
    def test_work_on_main_is_not_charged_to_the_next_change(self):
        run(["git", "checkout", "-q", "-b", "feature/elsewhere"], self.root)  # not main: CI's default may be master
        self.add_lines([user("2026-10-09T09:00:00Z"), assistant("msg_main", "2026-10-09T09:30:00Z", out=9999)])
        self.hook("Stop")
        run(["git", "checkout", "-q", "change/001-demo"], self.root)
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=7)])
        self.hook("Stop")
        [r] = self.records("usage")
        self.assertEqual((int(r["output"]), int(r["seconds"])), (7, 5))

    def test_usage_goes_to_the_branch_active_at_stop(self):
        other = os.path.join(self.root, "docs", "changes", "002-other")
        os.makedirs(other)
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=5)])
        self.hook("Stop")
        run(["git", "checkout", "-q", "-b", "change/002-other"], self.root)
        self.add_lines([user("2026-10-09T10:01:00Z"), assistant("msg_2", "2026-10-09T10:01:05Z", out=6)])
        self.hook("Stop")
        self.assertEqual([int(r["output"]) for r in self.records("usage")], [5])
        recs, _ = activity.read_records(os.path.join(other, "activity.log"))
        self.assertEqual([int(r["output"]) for r in recs], [6])

    def test_missing_folder_runs_hook_and_writes_nothing(self):
        run(["git", "checkout", "-q", "-b", "change/009-missing"], self.root)
        self.assertEqual(self.tool("Read", {"file_path": "pod.yml"}).returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs", "changes", "009-missing")))


class TranscriptProblemTests(ActivityRepo):
    def test_missing_transcript_recorded_as_unknown(self):
        os.remove(self.transcript)
        self.hook("Stop")
        [r] = self.records("usage")
        self.assertEqual((r["tokens"], r["usd"]), ("unknown", "unknown"))

    def test_rewritten_transcript_counts_old_messages_once(self):
        self.add_lines([assistant("msg_1", "2026-10-09T10:00:05Z", out=100),
                        assistant("msg_2", "2026-10-09T10:00:06Z", out=200)])
        self.hook("Stop")
        with open(self.transcript, "w", encoding="utf-8") as fh:
            for r in (assistant("msg_2", "2026-10-09T10:00:06Z", out=200),
                      assistant("msg_3", "2026-10-09T10:05:00Z", out=3)):
                fh.write(json.dumps(r) + "\n")
        res = self.hook("Stop")
        self.assertEqual([int(r["output"]) for r in self.records("usage")], [300, 3])
        self.assertIn("got shorter", res.stderr)

    def test_damaged_cursor_is_reset_with_warning(self):
        self.add_lines([assistant("msg_1", "2026-10-09T10:00:05Z", out=100)])
        self.hook("Stop")
        folder = os.path.join(self.root, ".pod", "activity")
        with open(os.path.join(folder, "sess-1.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        res = self.hook("Stop")
        self.assertEqual(res.returncode, 0)
        self.assertIn("read position for this session was damaged", res.stderr)
        self.assertEqual(len(self.records("usage")), 1)  # never counted twice: the reset skips to the end

    def test_idle_time_between_prompts_is_not_agent_time(self):
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:10Z", out=1),
                        tool_result("2026-10-09T10:00:12Z"), assistant("msg_2", "2026-10-09T10:00:20Z", out=1),
                        user("2026-10-09T11:00:00Z"), assistant("msg_3", "2026-10-09T11:00:05Z", out=1)])
        self.hook("Stop")
        self.assertEqual(sum(int(r["seconds"]) for r in self.records("usage")), 25)


class PriceTableTests(ActivityRepo):
    def test_missing_price_table(self):
        os.remove(os.path.join(self.root, "docs", "model-prices"))
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=100)])
        self.hook("Stop")
        res = self.sh("activity.sh", self.change)
        self.assertIn("cost: unknown (docs/model-prices not found)", res.stdout)

    def test_malformed_price_table_warns(self):
        with open(os.path.join(self.root, "docs", "model-prices"), "w", encoding="utf-8") as fh:
            fh.write("claude-opus-5-5 four twenty\n")
        self.add_lines([assistant("msg_1", "2026-10-09T10:00:05Z", out=10)])
        res = self.hook("Stop")
        self.assertIn("%s has no price in docs/model-prices" % OPUS, res.stderr)


class PrivacyTests(ActivityRepo):
    def test_unparseable_command_logs_no_part_of_a_secret(self):
        self.tool("Bash", {"command": 'TOKEN="ghp_abc defsecret" gh pr create --body don\'t'})
        r = self.records("tool")[0]
        self.assertEqual(r["cmd"], "?")
        self.assertNotIn("defsecret", self.log_text())

    def test_newline_in_a_value_cannot_forge_a_record(self):
        self.tool("Write", {"file_path": os.path.join(self.root, "a\nevent=usage model=m usd=99999 z=\nb"),
                            "content": "x"})
        self.assertEqual(self.records("usage"), [])
        self.assertEqual(len(self.records("tool")), 1)
        self.assertEqual(len(self.log_text().splitlines()), 1)

    def test_mcp_tool_path_is_not_logged(self):
        self.tool("mcp__docs__read", {"path": "users/alice@example.com"})
        r = self.records("tool")[0]
        self.assertNotIn("files", r)
        self.assertNotIn("alice", self.log_text())

    def test_file_contents_never_logged(self):
        self.tool("Edit", {"file_path": "app/x.py", "old_string": "OLD-CONTENT-XYZ", "new_string": "NEW-CONTENT-XYZ"})
        self.tool("Write", {"file_path": "app/y.py", "content": "WRITTEN-CONTENT-XYZ"}, tool_id="toolu_2")
        for needle in ("OLD-CONTENT", "NEW-CONTENT", "WRITTEN-CONTENT"):
            self.assertNotIn(needle, self.log_text())


class ViewingTests(ActivityRepo):
    def test_activity_time_line_and_metrics_order(self):
        self.tool("Read", {"file_path": "pod.yml"})
        self.add_lines([user("2026-10-09T10:00:00Z"), assistant("msg_1", "2026-10-09T10:00:05Z", out=1)])
        self.hook("Stop")
        out = self.sh("activity.sh", self.change).stdout
        self.assertRegex(out, r"activity: \d{4}-\d\d-\d\d \d\d:\d\d → \d{4}-\d\d-\d\d \d\d:\d\d   sessions: 1")
        lines = self.sh("metrics.sh", self.change).stdout.splitlines()
        lead = [i for i, l in enumerate(lines) if l.startswith("lead time")][0]
        self.assertTrue(lines[lead + 1].startswith("agent time:"))
        self.assertTrue(lines[lead + 2].startswith("agent cost:"))

    def test_metrics_when_off(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("activity_log: off\n")
        self.assertIn("agent cost: off (activity_log: off)", self.sh("metrics.sh", self.change).stdout)

    def test_two_sessions_and_conflict_markers(self):
        with open(self.log_path(), "w", encoding="utf-8") as fh:
            fh.write("event=tool at=2026-10-09T10:00:00Z session=a id=t1 tool=Read\n<<<<<<< HEAD\n"
                     "event=tool at=2026-10-09T10:00:01Z session=b id=t2 tool=Read\n>>>>>>> other\n")
        out = self.sh("activity.sh", self.change).stdout
        self.assertIn("sessions: 2", out)
        self.assertIn("skipped lines: 2", out)


class SetupTests(ActivityRepo):
    def test_hooks_registered_for_every_event_in_both_plugins(self):
        for hooks in (HOOKS_DEV, HOOKS_BIZ):
            with open(os.path.join(hooks, "hooks.json"), encoding="utf-8") as fh:
                config = json.load(fh)["hooks"]
            for event in ("PostToolUse", "Stop", "SubagentStop", "SessionEnd"):
                commands = [h["command"] for entry in config[event] for h in entry["hooks"]]
                self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/activity.sh"', commands, (hooks, event))
            self.assertTrue(os.access(os.path.join(hooks, "activity.sh"), os.X_OK))

    def test_older_kit_without_activity_py_is_silent(self):
        os.remove(os.path.join(self.root, "scripts", "activity.py"))
        res = self.tool("Read", {"file_path": "pod.yml"})
        self.assertEqual((res.returncode, res.stderr), (0, ""))
        self.assertFalse(os.path.exists(self.log_path()))

    def test_log_survives_a_global_log_ignore(self):
        with open(os.path.join(self.root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("*.log\n!docs/changes/*/gates.log\n!docs/changes/*/activity.log\n")
        self.tool("Read", {"file_path": "pod.yml"})
        res = run(["git", "check-ignore", "-q", self.log_path()], self.root)
        self.assertEqual(res.returncode, 1)
