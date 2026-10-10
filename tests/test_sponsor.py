"""Tests for change 003: sponsor controls (budget, ceiling, automatic stops, daily digest)."""
import json
import os
import re
import shutil

from tests.test_agent_seats import AUTONOMOUS, OPUS, SONNET, SeatRepo
from tests.test_pod_scripts import BIZ, DEV, HOOKS_DEV, POD, run
from tests.test_pod_v2 import AutoMergeRepo, git

NOW = "2026-10-10T12:00:00+00:00"
SPONSOR = "sam@example.com"


def usage(at, usd, session="u1", model=OPUS, source=""):
    return ("event=usage at=%s session=%s agent=main model=%s input=1 output=1 cache_write=0 cache_write_1h=0 "
            "cache_read=0 usd=%s seconds=1%s" % (at, session, model, usd, " source=" + source if source else ""))


def verdict(at, gate, result, run_id):
    return "event=verdict at=%s run=%s gate=%d role=owner by=agent:superbiz model=%s verdict=%s" % (
        at, run_id, gate, SONNET, result)


class SponsorRepo(SeatRepo):
    """Autonomous pod on change/001-demo (gate 1 signed by people), with a fixed clock and optional limits."""

    def setUp(self):
        super().setUp()
        self.env["TRIPOD_NOW"] = NOW
        # gate 1 was signed with the real clock; pin it before the fixed test times, so results never depend
        # on the time of day the tests run
        path = os.path.join(self.change, "gates.log")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(re.sub(r" at=\S+", " at=2026-10-10T00:00:00+00:00", text))

    def limits(self, text):
        self.set_mode(AUTONOMOUS + text)

    def add_activity(self, change, *lines):
        with open(os.path.join(change, "activity.log"), "a", encoding="utf-8") as fh:
            fh.write("".join(l + "\n" for l in lines))

    def add_log(self, change, *lines):
        with open(os.path.join(change, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("".join(l + "\n" for l in lines))

    def other_change(self, slug="002-other"):
        path = os.path.join(self.root, "docs", "changes", slug)
        os.makedirs(path, exist_ok=True)
        return path

    def script(self, name, *args, email=None):
        env = dict(self.env)
        if email:
            env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.email", "GIT_CONFIG_VALUE_0": email})
        return run([os.path.join(self.root, "scripts", name)] + list(args), self.root, env=env)


# ---------- R1: limits in pod.yml ----------

class LimitConfigTests(SponsorRepo):
    def test_malformed_limits_fail_gate_check(self):
        self.limits("budget_per_day_usd: abc\nmax_refusals_per_gate: -1\n")
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("pod.yml: budget_per_day_usd: abc is not a number", res.stdout)
        self.assertIn("pod.yml: max_refusals_per_gate: -1 must not be negative", res.stdout)

    def test_malformed_limit_refuses_agent_sign(self):
        self.limits("budget_per_change_usd: lots\n")
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("budget_per_change_usd: lots is not a number", res.stdout)
        self.assertEqual(self.calls(), [])

    def test_no_keys_no_limits(self):
        self.add_activity(self.change, usage("2026-10-10T11:00:00Z", "999.00"))
        self.assertEqual(self.agent_sign(2).returncode, 0)


# ---------- R3, R4, E4, E5: budget ----------

class BudgetTests(SponsorRepo):
    def test_change_budget_with_estimate(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.900000", "a", source="agent-sign"),
                          usage("2026-10-09T10:00:00Z", "0.200000", "b", source="agent-sign"))
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: budget for 001-demo reached: spent US$1.10 of US$1.00 (budget_per_change_usd), "
                      "and the next check may cost about US$0.90", res.stdout)
        self.assertEqual(self.calls(), [])

    def test_estimate_is_the_most_expensive_recent_run(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.30", "a", source="agent-sign"),
                          usage("2026-10-10T10:00:00Z", "0.10", "a", model=SONNET, source="agent-sign"),
                          usage("2026-10-01T10:00:00Z", "5.00", "old", source="agent-sign"))  # older than 7 days
        res = self.agent_sign(2)
        self.assertIn("spent US$5.40 of US$1.00", res.stdout)
        self.assertIn("next check may cost about US$0.40", res.stdout)

    def test_exactly_on_budget_is_allowed(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.50", "a", source="agent-sign"))
        self.assertEqual(self.agent_sign(2).returncode, 0)  # 0.50 spent + 0.50 estimate = 1.00

    def test_no_earlier_run_means_estimate_zero(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "0.99"))  # a hook record, not agent-sign
        self.assertEqual(self.agent_sign(2).returncode, 0)

    def test_day_budget_across_changes(self):
        self.limits("budget_per_day_usd: 2.00\n")
        other = self.other_change()
        self.add_activity(other, usage("2026-10-10T01:00:00Z", "1.50"), usage("2026-10-09T11:00:00Z", "9.00"))
        self.add_activity(self.change, usage("2026-10-10T11:00:00Z", "0.60", "a", source="agent-sign"))
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: today's budget reached: spent US$2.10 in the last 24 hours of US$2.00 "
                      "(budget_per_day_usd), next check about US$0.60", res.stdout)

    def test_unknown_cost_counts_as_zero(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "unknown"), usage("2026-10-10T10:00:00Z", "abc"))
        self.assertEqual(self.agent_sign(2).returncode, 0)

    def test_people_are_never_limited(self):
        self.limits("budget_per_change_usd: 0.01\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "5.00"))
        self.edit(self.change, "spec.md", "# spec\n")
        self.assertEqual(self.approve(self.change, 2, BIZ).returncode, 0)


# ---------- R5, R7: refusals in a row and resume ----------

class RefusalStopTests(SponsorRepo):
    def setUp(self):
        super().setUp()
        self.limits("max_refusals_per_gate: 2\n")
        self.add_activity(self.change, verdict("2026-10-10T10:00:00Z", 2, "refuse", "r1"),
                          verdict("2026-10-10T10:05:00Z", 2, "refuse", "r2"))

    def test_stops_after_max(self):
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: gate 2 has 2 refused agent checks since a person last acted (max_refusals_per_gate: 2). "
                      "A person reviews it, then runs scripts/resume.sh", res.stdout)
        self.assertEqual(self.calls(), [])

    def test_other_gate_not_affected(self):
        self.add_activity(self.change, verdict("2026-10-10T10:06:00Z", 3, "approve", "r3"))
        self.assertIn("gate 2 has 2 refused", self.agent_sign(2).stdout)

    def test_resume_by_a_member(self):
        res = self.script("resume.sh", self.change, "spec reviewed, try again", email=BIZ)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("Resumed: 001-demo (agent checks may run again on every gate)", res.stdout)
        self.assertRegex(self.lines()[-1], r'^event=resume by=%s at=\S+ reason="spec reviewed, try again"$' % BIZ)
        self.assertEqual(self.agent_sign(2).returncode, 0)

    def test_resume_by_the_sponsor(self):
        self.assertEqual(self.script("resume.sh", self.change, "ok", email=SPONSOR).returncode, 0)

    def test_resume_by_a_stranger_is_refused(self):
        res = self.script("resume.sh", self.change, "let me", email="x@example.com")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: git email 'x@example.com' is not the sponsor or a member in pod.yml",
                      res.stdout + res.stderr)

    def test_a_person_signing_resets(self):
        self.edit(self.change, "spec.md", "# spec\n- R1: the system must add numbers\n")
        self.add_log(self.change, "gate=2 role=owner by=%s at=2026-10-10T11:00:00+00:00 blob=%s"
                     % (BIZ, self.blob(self.change, "spec.md")))
        self.assertEqual(self.agent_sign(2).returncode, 0)


# ---------- R6: revert ----------

class RevertStopTests(SponsorRepo):
    def test_recent_revert_pauses_agents(self):
        self.add_log(self.other_change(), 'event=revert by=%s at=2026-10-10T02:00:00+00:00 reason="broke"' % DEV)
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: 002-other was reverted at 2026-10-10 02:00 UTC; agents pause for 24 hours after a revert "
                      "(until 2026-10-11 02:00 UTC)", res.stdout)

    def test_old_revert_does_not(self):
        self.add_log(self.other_change(), 'event=revert by=%s at=2026-10-09T11:00:00+00:00 reason="old"' % DEV)
        self.assertEqual(self.agent_sign(2).returncode, 0)


# ---------- R8, R9: risk ceiling ----------

class CeilingTests(SponsorRepo):
    def test_forbidden_path_refused_by_agent_sign(self):
        with open(os.path.join(self.root, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write("__pycache__/\n")
        self.limits("agent_forbidden_paths: app/billing*, docs/legal/**\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "so far")
        git(self.root, "branch", "-f", "main", "HEAD")
        os.makedirs(os.path.join(self.root, "app"), exist_ok=True)
        with open(os.path.join(self.root, "app", "billing.py"), "w", encoding="utf-8") as fh:
            fh.write("X = 1\n")
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: this change touches app/billing.py, which agents may not change "
                      "(agent_forbidden_paths); people sign it", res.stdout)


class CeilingAutoMergeTests(AutoMergeRepo):
    def test_forbidden_path_denied_at_merge(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("agent_forbidden_paths: app/calc.py\n")
        self.assert_deny("touches app/calc.py, which agents may not change (agent_forbidden_paths); people merge it")

    def test_merges_per_day(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("agent_merges_per_day: 1\n")
        other = self.history[0]
        with open(os.path.join(other, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("gate=4 role=auto by=auto-merge at=2026-10-10T08:00:00+00:00 blob=- head=%s\n" % ("0" * 40))
        os.environ["TRIPOD_NOW"] = NOW
        self.addCleanup(os.environ.pop, "TRIPOD_NOW", None)
        self.assert_deny("1 changes were auto-merged in the last 24 hours (agent_merges_per_day: 1); "
                         "people merge this one")


# ---------- R10: warning in the agent's session ----------

class HookWarningTests(SponsorRepo):
    def hook(self, session="sess-x", tool_id="t1"):
        data = {"session_id": session, "transcript_path": os.path.join(self.root, "none.jsonl"), "cwd": self.root,
                "hook_event_name": "PostToolUse", "tool_name": "Read", "tool_input": {"file_path": "pod.yml"},
                "tool_use_id": tool_id}
        env = {"CLAUDE_PROJECT_DIR": self.root, "TRIPOD_NOW": NOW}
        return run([os.path.join(HOOKS_DEV, "activity.sh")], self.root, env=env, stdin=json.dumps(data))

    def test_warns_once_per_session_per_limit(self):
        self.limits("budget_per_change_usd: 1.00\n")
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "1.20"))
        res = self.hook()
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn("Tripod: the change budget is reached (US$1.20 of US$1.00). scripts/agent-sign.sh will refuse "
                      "until the sponsor raises it. Finish the current step and hand over",
                      out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook(tool_id="t2").stdout.strip(), "")
        self.assertIn("additionalContext", self.hook(session="sess-y", tool_id="t3").stdout)

    def test_silent_under_budget_or_without_limits(self):
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "1.20"))
        self.assertEqual(self.hook().stdout.strip(), "")
        self.limits("budget_per_change_usd: 5.00\n")
        self.assertEqual(self.hook(tool_id="t2").stdout.strip(), "")


# ---------- R11, R12: digest ----------

class DigestTests(SponsorRepo):
    def fill(self):
        self.limits("budget_per_day_usd: 5.00\nmax_refusals_per_gate: 3\n")
        other = self.other_change()
        self.add_activity(self.change, usage("2026-10-10T10:00:00Z", "1.25", "a", OPUS, "agent-sign"),
                          usage("2026-10-10T10:00:00Z", "0.50", "a", SONNET, "agent-sign"),
                          usage("2026-10-10T09:00:00Z", "unknown", "h", "claude-x"),
                          usage("2026-10-08T09:00:00Z", "7.00", "old"),
                          verdict("2026-10-10T10:00:00Z", 2, "refuse", "a"))
        self.add_activity(other, usage("2026-10-10T08:00:00Z", "0.25", "o", SONNET))
        b = self.blob(self.change, "spec.md")
        self.add_log(self.change,
                     "gate=2 role=owner by=agent:superbiz model=%s session=a at=2026-10-10T10:01:00+00:00 blob=%s" % (SONNET, b),
                     'event=resume by=%s at=2026-10-10T10:30:00+00:00 reason="checked"' % SPONSOR)
        self.add_log(other, "gate=4 role=auto by=auto-merge at=2026-10-10T07:00:00+00:00 blob=- head=%s" % ("0" * 40),
                     'event=revert by=%s at=2026-10-10T07:30:00+00:00 reason="broke the page"' % DEV)

    def digest(self, *args):
        return self.script("digest.sh", *args)

    def test_digest_matches_the_logs(self):
        self.fill()
        res = self.digest()
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout
        self.assertIn("Tripod digest, last 24 hours (2026-10-09 12:00 → 2026-10-10 12:00 UTC)", out)
        self.assertIn("spend: US$2.00 (limit US$5.00 per day) · unknown: 1 records", out)
        self.assertIn("001-demo US$1.75 (claude-opus-5-5 US$1.25, claude-sonnet-5-5 US$0.50)", out)
        self.assertIn("002-other US$0.25 (claude-sonnet-5-5 US$0.25)", out)
        self.assertIn("agent signatures: 001-demo gate 2 owner claude-sonnet-5-5", out)
        self.assertIn("refused agent checks: 001-demo 1 (gate 2: 1)", out)
        self.assertIn("auto-merges: 002-other at 2026-10-10 07:00", out)
        self.assertIn("reverts: 002-other at 2026-10-10 07:30 by %s: broke the page" % DEV, out)
        self.assertIn("resumes: 001-demo at 2026-10-10 10:30 by %s: checked" % SPONSOR, out)
        self.assertIn("stops in force: 002-other reverted at 2026-10-10 07:30 UTC; agents pause until 2026-10-11 07:30 UTC", out)
        self.assertIn("limits: budget_per_day_usd 5.00, max_refusals_per_gate 3", out)

    def test_hours_window(self):
        self.fill()
        self.assertIn("spend: US$1.75", self.digest("--hours", "3").stdout)  # since 09:00: leaves out 08:00

    def test_empty(self):
        shutil.rmtree(os.path.join(self.root, "docs", "changes"))
        os.makedirs(os.path.join(self.root, "docs", "changes"))
        out = self.digest().stdout
        self.assertIn("spend: US$0.00", out)
        self.assertIn("auto-merges: nothing in the last 24 hours", out)
        self.assertIn("stops in force: nothing in the last 24 hours", out)
        self.assertIn("limits: none set", out)

    def test_write(self):
        self.fill()
        res = self.digest("--write")
        path = os.path.join(self.root, "docs", "digest", "2026-10-10.md")
        self.assertTrue(os.path.exists(path), res.stdout + res.stderr)
        with open(path, encoding="utf-8") as fh:
            self.assertIn("spend: US$2.00", fh.read())
        self.digest("--write")  # same day: overwritten, not appended
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read().count("Tripod digest"), 1)

    def test_bad_time_is_skipped_and_counted(self):
        self.add_activity(self.change, usage("not-a-time", "1.00"))
        self.assertIn("skipped records: 1", self.digest().stdout)


# ---------- installer and docs ----------

class SponsorSetupTests(SponsorRepo):
    def test_template_documents_the_keys(self):
        with open(os.path.join(POD, "docs", "templates", "pod.yml"), encoding="utf-8") as fh:
            text = fh.read()
        for key in ("budget_per_change_usd", "budget_per_day_usd", "max_refusals_per_gate", "agent_merges_per_day",
                    "agent_forbidden_paths"):
            self.assertIn(key, text)

    def test_agents_md_forbids_resume(self):
        with open(os.path.join(POD, "AGENTS.md"), encoding="utf-8") as fh:
            self.assertIn("scripts/resume.sh", fh.read())
