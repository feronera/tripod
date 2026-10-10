"""Tests added at review for change 003 (approved by the PO while tests/test_sponsor.py stays locked).
They cover the review findings: the test clock (B1), logs on the base branch (M1), forged resumes and
signatures (M2), bad amounts and times (M3, M4), the price file (M5), symlinks (M6), renames (M7), the
merges-per-day count, the digest using the same stops as agent-sign, and the hook's fast path."""
import datetime
import json
import os
import sys
import tempfile

from tests.test_pod_scripts import BIZ, DEV, HOOKS_DEV, POD, run
from tests.test_pod_v2 import AutoMergeRepo, git
from tests.test_sponsor import NOW, SponsorRepo, usage, verdict

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402
import sponsor  # noqa: E402


class ClockTests(SponsorRepo):
    def with_now(self, value):
        old = os.environ.get("TRIPOD_NOW")
        os.environ["TRIPOD_NOW"] = value
        self.addCleanup(lambda: os.environ.__setitem__("TRIPOD_NOW", old) if old else os.environ.pop("TRIPOD_NOW", None))

    def test_a_future_clock_is_ignored(self):
        self.with_now("2099-01-01T00:00:00+00:00")
        self.assertLessEqual(sponsor.now(), datetime.datetime.now(datetime.timezone.utc))

    def test_a_past_clock_only_makes_stops_stricter(self):
        self.add_log(self.other_change(), 'event=revert by=%s at=2026-10-10T09:00:00+00:00 reason="x"' % DEV)
        self.with_now("2000-01-01T00:00:00+00:00")
        at = sponsor.now()
        events, _ = sponsor.ledger(self.root, at)
        self.assertIsNotNone(sponsor.recent_revert(events, at))  # a later event is still in the window

    def test_future_clock_cannot_skip_a_stop(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "5.00"))
        res = self.agent_sign(2, TRIPOD_NOW="2099-01-01T00:00:00+00:00")
        self.assertEqual(res.returncode, 1)
        self.assertIn("budget for 001-demo reached", res.stdout)

    def test_offsets_are_converted_to_utc(self):  # E6
        self.add_log(self.other_change(), 'event=revert by=%s at=2026-10-10T16:00:00+07:00 reason="x"' % DEV)
        self.assertIn("(until 2026-10-11 09:00 UTC)", self.agent_sign(2).stdout)


class BaseBranchTests(SponsorRepo):
    def test_revert_on_main_pauses_every_branch(self):
        other = self.other_change()
        self.add_log(other, 'event=revert by=%s at=2026-10-10T09:00:00+00:00 reason="on main"' % DEV)
        git(self.root, "add", other)
        git(self.root, "commit", "-q", "-m", "revert on main")
        git(self.root, "branch", "-f", "main", "HEAD")
        git(self.root, "reset", "-q", "--hard", "HEAD~1")  # this branch does not have it yet
        self.assertFalse(os.path.exists(other))
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("002-other was reverted at 2026-10-10 09:00 UTC", res.stdout)


class IdentityTests(SponsorRepo):
    def setUp(self):
        super().setUp()
        self.limits("max_refusals_per_gate: 2\n")
        self.add_activity(self.change, verdict("2026-10-10T10:00:00Z", 2, "refuse", "r1"),
                          verdict("2026-10-10T10:05:00Z", 2, "refuse", "r2"))

    def test_forged_resume_does_not_reset(self):
        self.add_log(self.change, 'event=resume by=agent:superdev at=2026-10-10T11:00:00+00:00 reason="me"')
        self.assertIn("gate 2 has 2 refused", self.agent_sign(2).stdout)

    def test_signature_by_a_stranger_does_not_reset(self):
        self.add_log(self.change, "gate=2 role=owner by=nobody@x at=2026-10-10T11:00:00+00:00 blob=bogus")
        self.assertIn("gate 2 has 2 refused", self.agent_sign(2).stdout)

    def test_resume_does_not_lift_a_budget_or_a_revert(self):  # R7
        self.limits("max_refusals_per_gate: 2\nbudget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "5.00"))
        self.add_log(self.other_change(), 'event=revert by=%s at=2026-10-10T09:00:00+00:00 reason="x"' % DEV)
        self.assertEqual(self.script("resume.sh", self.change, "ok", email=BIZ).returncode, 0)
        out = self.agent_sign(2).stdout
        self.assertIn("budget for 001-demo reached", out)
        self.assertIn("was reverted", out)
        self.assertNotIn("refused agent checks", out)

    def test_resume_only_inside_docs_changes(self):
        outside = tempfile.mkdtemp()
        res = self.script("resume.sh", outside, "x", email=BIZ)
        self.assertEqual(res.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(outside, "gates.log")))


class AmountTests(SponsorRepo):
    def test_nan_negative_and_infinite_amounts_are_unknown(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "5.00"), usage("2026-10-10T10:00:00Z", "nan"),
                          usage("2026-10-10T10:00:00Z", "-100"), usage("2026-10-10T10:00:00Z", "inf"))
        self.assertIn("spent US$5.00 of US$1.00", self.agent_sign(2).stdout)
        self.assertIn("unknown: 3 records", self.script("digest.sh").stdout)

    def test_bad_time_still_counts_for_the_change(self):  # E2
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("not-a-time", "5.00"))
        self.assertIn("spent US$5.00 of US$1.00", self.agent_sign(2).stdout)

    def test_nan_limit_is_rejected(self):
        self.limits("budget_per_day_usd: nan\n")
        self.assertIn("budget_per_day_usd: nan is not a number", self.check("--all").stdout)

    def test_over_budget_with_no_estimate_refuses(self):  # E5
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "1.50"))
        self.assertIn("next check may cost about US$0.00", self.agent_sign(2).stdout)


class FileTests(SponsorRepo):
    def test_price_file_is_a_governance_file(self):  # M5
        self.assertEqual(lib.governance_files(["docs/model-prices", "app/x.py"]), ["docs/model-prices"])

    def test_digest_write_refuses_a_symlink(self):  # M6
        target = tempfile.mkdtemp()
        os.symlink(target, os.path.join(self.root, "docs", "digest"))
        res = self.script("digest.sh", "--write")
        self.assertEqual(res.returncode, 1)
        self.assertEqual(os.listdir(target), [])

    def test_rename_out_of_a_forbidden_path(self):  # M7
        with open(os.path.join(self.root, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write("__pycache__/\n")
        self.limits("agent_forbidden_paths: app/billing*\n")
        os.makedirs(os.path.join(self.root, "app"), exist_ok=True)
        with open(os.path.join(self.root, "app", "billing.py"), "w", encoding="utf-8") as fh:
            fh.write("RATE = 1\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "so far")
        git(self.root, "branch", "-f", "main", "HEAD")
        git(self.root, "mv", "app/billing.py", "app/plain.py")
        git(self.root, "commit", "-q", "-m", "move")
        self.assertIn("touches app/billing.py", self.agent_sign(2).stdout)


class DigestStopTests(SponsorRepo):
    def test_digest_lists_the_same_stops_as_agent_sign(self):
        self.limits("budget_per_change_usd: 1.00\nmax_refusals_per_gate: 2\nbudget_per_day_usd: 1.00\n")
        path = os.path.join(self.change, "gates.log")  # people last acted before the old refusals
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace("at=2026-10-10T00:00:00+00:00", "at=2026-10-01T00:00:00+00:00"))
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.70", "a", source="agent-sign"),
                          verdict("2026-10-08T10:00:00Z", 3, "refuse", "o1"),  # outside the 24-hour window
                          verdict("2026-10-08T10:05:00Z", 3, "refuse", "o2"))
        out = self.script("digest.sh").stdout
        self.assertIn("budget for 001-demo reached: spent US$0.70 of US$1.00", out)  # 0.70 + 0.70 estimate
        self.assertIn("001-demo: gate 3 has 2 refused agent checks", out)
        self.assertIn("today's budget reached: spent US$0.70 in the last 24 hours of US$1.00", out)
        self.assertIn("budget for 001-demo reached", self.agent_sign(2).stdout)

    def test_digest_in_pod_mode(self):  # E7
        self.write_pod_yml()
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.40"))
        res = self.script("digest.sh")
        self.assertEqual(res.returncode, 0)
        self.assertIn("spend: US$0.40", res.stdout)


class MergesPerDayTests(AutoMergeRepo):
    def setUp(self):
        super().setUp()
        os.environ["TRIPOD_NOW"] = NOW
        self.addCleanup(os.environ.pop, "TRIPOD_NOW", None)

    def auto_line(self, change):
        with open(os.path.join(change, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("gate=4 role=auto by=auto-merge at=2026-10-10T08:00:00+00:00 blob=- head=%s\n" % ("0" * 40))

    def test_own_record_is_not_counted(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("agent_merges_per_day: 1\n")
        self.auto_line(self.c)  # CI re-checks a change that already carries its auto record
        res = self.auto()
        self.assertNotIn("auto-merged in the last 24 hours", res.stdout)

    def test_a_change_counts_once(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("agent_merges_per_day: 2\n")
        self.auto_line(self.history[0])
        self.auto_line(self.history[0])
        self.assertNotIn("auto-merged in the last 24 hours", self.auto().stdout)


class HookSpeedPathTests(SponsorRepo):
    def test_day_warning(self):  # R10, the day limit
        self.limits("budget_per_day_usd: 1.00\n")
        self.add_activity(self.other_change(), usage("2026-10-10T11:00:00Z", "2.00"))
        data = {"session_id": "s1", "transcript_path": "none", "cwd": self.root, "hook_event_name": "PostToolUse",
                "tool_name": "Read", "tool_input": {"file_path": "pod.yml"}, "tool_use_id": "t1"}
        res = run([os.path.join(HOOKS_DEV, "activity.sh")], self.root,
                  env={"CLAUDE_PROJECT_DIR": self.root, "TRIPOD_NOW": NOW}, stdin=json.dumps(data))
        self.assertIn("Tripod: the day budget is reached (US$2.00 of US$1.00)",
                      json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_usage_spend_reads_only_the_window(self):
        path = os.path.join(self.change, "activity.log")
        self.add_activity(self.change, usage("2026-10-08T10:00:00Z", "9.00"), usage("2026-10-10T10:00:00Z", "1.00"),
                          "event=tool at=2026-10-10T10:01:00Z session=s id=t tool=Read")
        since = sponsor.parse_at("2026-10-09T12:00:00Z")
        self.assertAlmostEqual(sponsor.usage_spend(path, since), 1.00)
        self.assertAlmostEqual(sponsor.usage_spend(path), 10.00)
