"""Tests for change 002: agent seats and agent signatures (Autonomous mode for low risk)."""
import json
import os
import stat
import sys

from tests.test_pod_scripts import BIZ, DEV, POD, VALID_PLAN, PodRepo, run
from tests.test_pod_v2 import AutoMergeRepo, git

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402

SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"
AUTONOMOUS = ("mode: autonomous\nsuperbiz_agent_model: %s\nsuperdev_agent_model: %s\n"
              "sponsor_name: Sam\nsponsor_email: sam@example.com\nsponsor_github: sam-gh\n" % (SONNET, OPUS))

# A stand-in for `claude -p`: prints the JSON result Claude Code would print, and logs its arguments.
FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
log = os.environ["FAKE_CLAUDE_LOG"]
with open(log, "a") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\n")
if os.environ.get("FAKE_EXIT"):
    print("boom", file=sys.stderr)
    sys.exit(int(os.environ["FAKE_EXIT"]))
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-default"
model = os.environ.get("FAKE_MODEL", model)
n = sum(1 for _ in open(log))
session = "sess-%d" % n
if os.environ.get("FAKE_HOOK_LOG"):  # the plugin hooks already wrote usage for this session
    with open(os.environ["FAKE_HOOK_LOG"], "a") as fh:
        fh.write("event=usage at=2026-10-10T10:00:00Z session=%s agent=main model=%s input=1 output=1 "
                 "cache_write=0 cache_write_1h=0 cache_read=0 usd=0.000024 seconds=1\n" % (session, model))
result = os.environ.get("FAKE_RESULT", "Q1: yes, every requirement can be tested.\nVERDICT: APPROVE")
print(json.dumps({"type": "result", "session_id": session, "result": result, "total_cost_usd": 0.05,
                  "modelUsage": {model: {"inputTokens": 10, "outputTokens": 20, "cacheReadInputTokens": 0,
                                         "cacheCreationInputTokens": 0, "costUSD": 0.05}}}))
'''


class SeatRepo(PodRepo):
    """A pod repo in Autonomous mode, on branch change/001-demo, with gate 1 signed by people."""

    def setUp(self):
        super().setUp()
        for name in ("gates.md",):
            src = os.path.join(POD, "docs", name)
            with open(src, encoding="utf-8") as fh, \
                    open(os.path.join(self.root, "docs", name), "w", encoding="utf-8") as out:
                out.write(fh.read())
        self.set_mode(AUTONOMOUS)
        self.change = self.new_change("demo")
        run(["git", "add", "-A"], self.root)
        run(["git", "commit", "-q", "-m", "base"], self.root)
        run(["git", "checkout", "-q", "-b", "change/001-demo"], self.root)
        self.pass_gate(self.change, 1)
        self.edit(self.change, "spec.md", "# spec\n- R1: the system must add numbers\n")
        bin_dir = os.path.join(self.root, ".fakebin")
        os.makedirs(bin_dir)
        self.fake = os.path.join(bin_dir, "claude")
        with open(self.fake, "w", encoding="utf-8") as fh:
            fh.write(FAKE_CLAUDE)
        os.chmod(self.fake, os.stat(self.fake).st_mode | stat.S_IEXEC)
        self.calls_log = os.path.join(self.root, ".fakebin", "calls.log")
        self.env = {"TRIPOD_CLAUDE": self.fake, "FAKE_CLAUDE_LOG": self.calls_log}

    def set_mode(self, extra):
        self.write_pod_yml()
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write(extra)

    def agent_sign(self, gate, **env):
        full = dict(self.env)
        full.update(env)
        return run([os.path.join(self.root, "scripts", "agent-sign.sh"), self.change, str(gate)],
                   self.root, env=full)

    def calls(self):
        if not os.path.exists(self.calls_log):
            return []
        with open(self.calls_log, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh]

    def lines(self):
        with open(os.path.join(self.change, "gates.log"), encoding="utf-8") as fh:
            return fh.read().splitlines()

    def activity(self):
        path = os.path.join(self.change, "activity.log")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def sign_gate(self, gate):
        if gate == 3 and not os.path.exists(os.path.join(self.change, "plan.md")):
            self.edit(self.change, "plan.md", VALID_PLAN)
        if gate == 4 and not os.path.exists(os.path.join(self.change, "acceptance.md")):
            self.edit(self.change, "acceptance.md", "# acceptance\nDecision: accept\n")
        for _ in ("owner", "cross"):
            res = self.agent_sign(gate)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


# ---------- R1-R3: configuration ----------

class ConfigTests(SeatRepo):
    def test_pod_mode_is_default_and_refuses(self):
        self.write_pod_yml()
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: pod.yml sets mode: pod. Agents may sign only in mode: autonomous", res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_autonomous_needs_seat_models(self):
        self.set_mode(AUTONOMOUS.replace("superdev_agent_model: %s\n" % OPUS, ""))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("pod.yml: mode: autonomous needs superdev_agent_model", res.stdout)

    def test_autonomous_needs_different_models(self):
        self.set_mode(AUTONOMOUS.replace("superdev_agent_model: %s" % OPUS, "superdev_agent_model: %s" % SONNET))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("superbiz_agent_model and superdev_agent_model are both %s" % SONNET, res.stdout)
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_autonomous_needs_sponsor(self):
        self.set_mode(AUTONOMOUS.replace("sponsor_email: sam@example.com\n", ""))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("pod.yml: mode: autonomous needs sponsor_email", res.stdout)

    def test_valid_autonomous_config_passes(self):
        self.assertEqual(self.check("--all").returncode, 0)


# ---------- R4-R7, R14: agent-sign ----------

class SignTests(SeatRepo):
    def test_owner_then_cross(self):
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("Checking gate 2 as owner (agent:superbiz, %s)..." % SONNET, res.stdout)
        self.assertIn("APPROVE gate 2 owner (agent:superbiz, %s)" % SONNET, res.stdout)
        res = self.agent_sign(2)
        self.assertIn("APPROVE gate 2 cross (agent:superdev, %s)" % OPUS, res.stdout)
        lines = self.lines()
        self.assertEqual(sum(1 for l in lines if l.startswith("event=mode")), 1)
        self.assertRegex(lines[-2], r"^gate=2 role=owner by=agent:superbiz model=%s session=sess-1 at=\S+ blob=[0-9a-f]{40}$" % SONNET)
        self.assertRegex(lines[-1], r"^gate=2 role=cross by=agent:superdev model=%s session=sess-2 at=\S+ blob=[0-9a-f]{40}$" % OPUS)
        self.assertEqual(self.check(self.change, "2").returncode, 0)

    def test_starts_claude_with_seat_model_and_read_only_tools(self):
        self.agent_sign(2)
        [args] = self.calls()
        self.assertIn("-p", args)
        self.assertEqual(args[args.index("--model") + 1], SONNET)
        self.assertEqual(args[args.index("--output-format") + 1], "json")
        tools = args[args.index("--allowedTools") + 1]
        self.assertNotIn("Bash", tools)
        self.assertNotIn("Write", tools)
        prompt = args[args.index("-p") + 1]
        self.assertIn("VERDICT: APPROVE", prompt)
        self.assertIn("spec.md", prompt)

    def test_refuse_writes_nothing(self):
        before = self.lines()
        res = self.agent_sign(2, FAKE_RESULT="R1 is not testable.\nVERDICT: REFUSE")
        self.assertEqual(res.returncode, 1)
        self.assertIn("REFUSE gate 2 owner (agent:superbiz, %s)" % SONNET, res.stdout)
        self.assertIn("R1 is not testable", res.stdout)
        self.assertEqual(self.lines(), before)

    def test_unclear_verdict_counts_as_refuse(self):
        res = self.agent_sign(2, FAKE_RESULT="Looks fine to me")
        self.assertEqual(res.returncode, 1)
        self.assertIn("REFUSE gate 2 owner", res.stdout)

    def test_claude_failure_records_nothing(self):
        res = self.agent_sign(2, FAKE_EXIT="3")
        self.assertEqual(res.returncode, 1)
        self.assertIn("agent-sign: claude did not return a verdict", res.stdout + res.stderr)
        self.assertIn("Nothing was recorded", res.stdout + res.stderr)
        self.assertFalse(any("agent:" in l for l in self.lines()))

    def test_model_must_be_the_seat_model(self):
        res = self.agent_sign(2, FAKE_MODEL="claude-haiku-4-5")
        self.assertEqual(res.returncode, 1)
        self.assertIn(SONNET, res.stdout + res.stderr)
        self.assertFalse(any("agent:" in l for l in self.lines()))

    def test_refusals_before_start(self):
        cases = []
        self.edit(self.change, "intent.md", None, risk="medium")
        cases.append((2, "Refused: Risk is medium. Agents may sign only Risk: low changes; medium and high need people"))
        for gate, needle in cases:
            res = self.agent_sign(gate)
            self.assertEqual(res.returncode, 1)
            self.assertIn(needle, res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_gate_1_refused(self):
        res = self.agent_sign(1)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: gate 1 is always signed by people, who decide the risk", res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_previous_gate_incomplete_refused(self):
        self.edit(self.change, "plan.md", VALID_PLAN)
        res = self.agent_sign(3)
        self.assertEqual(res.returncode, 1)
        self.assertIn("gate 2 must be complete first", res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_missing_artifact_refused(self):
        os.remove(os.path.join(self.change, "spec.md"))
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("spec.md not found", res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_kill_switch(self):
        os.makedirs(os.path.join(self.root, ".pod"), exist_ok=True)
        open(os.path.join(self.root, ".pod", "kill-switch"), "w").close()
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: kill switch is on (.pod/kill-switch). No agent was started", res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])

    def test_gate_complete_refuses_more(self):
        self.sign_gate(2)
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("already complete", res.stdout + res.stderr)

    def test_evidence_written_when_hooks_did_not(self):
        self.agent_sign(2)
        self.assertRegex(self.activity(), r"event=usage .*session=sess-1 .*model=%s .*source=agent-sign" % SONNET)

    def test_no_duplicate_evidence_when_hooks_wrote_it(self):
        self.agent_sign(2, FAKE_HOOK_LOG=os.path.join(self.change, "activity.log"))
        usage = [l for l in self.activity().splitlines() if "session=sess-1" in l]
        self.assertEqual(len(usage), 1)
        self.assertNotIn("source=agent-sign", usage[0])


# ---------- R8-R11: gate-check ----------

class CheckTests(SeatRepo):
    def replace_line(self, old, new):
        path = os.path.join(self.change, "gates.log")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, new))

    def assert_problem(self, needle, gate="2"):
        res = self.check(self.change, gate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn(needle, res.stdout)

    def test_wrong_leg(self):
        self.sign_gate(2)
        self.replace_line("role=owner by=agent:superbiz", "role=owner by=agent:superdev")
        self.assert_problem("gate 2: owner must be signed by agent:superbiz, not agent:superdev")

    def test_wrong_model(self):
        self.sign_gate(2)
        self.replace_line("by=agent:superbiz model=%s" % SONNET, "by=agent:superbiz model=claude-haiku-4-5")
        self.assert_problem("gate 2: agent signature by agent:superbiz used claude-haiku-4-5, but pod.yml sets "
                            "superbiz_agent_model: %s" % SONNET)

    def test_no_evidence(self):
        self.sign_gate(2)
        os.remove(os.path.join(self.change, "activity.log"))
        self.assert_problem("gate 2: agent signature by agent:superbiz has no usage for session sess-1 with %s "
                            "in activity.log" % SONNET)

    def test_unknown_leg_and_missing_fields(self):
        self.sign_gate(2)
        self.replace_line("by=agent:superbiz", "by=agent:foo")
        self.assert_problem("gate 2: owner must be signed by agent:superbiz, not agent:foo")

    def test_not_allowed_when_risk_raised(self):
        self.sign_gate(2)
        self.edit(self.change, "intent.md", None, risk="medium")
        res = self.check(self.change, "2")
        self.assertEqual(res.returncode, 1)
        self.assertIn("gate 2: agent signature not allowed here (Risk: medium)", res.stdout)

    def test_gate_1_agent_line_rejected(self):
        b = self.blob(self.change, "intent.md")
        self.write_log(self.change, [
            "event=mode mode=autonomous at=2026-10-10T09:00:00Z",
            "gate=1 role=owner by=agent:superbiz model=%s session=s1 at=2026-10-10T09:00:00Z blob=%s" % (SONNET, b),
            "gate=1 role=cross by=agent:superdev model=%s session=s2 at=2026-10-10T09:01:00Z blob=%s" % (OPUS, b)])
        self.assert_problem("gate 1: agent signature not allowed here (gate 1 is signed by people)", gate="1")

    def test_mixed_person_and_agent(self):
        self.agent_sign(2)  # owner: agent:superbiz
        self.approve(self.change, 2, DEV)  # cross: the SuperDev person
        res = self.check(self.change, "2")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_stale_after_artifact_edit(self):
        self.sign_gate(2)
        self.edit(self.change, "spec.md", "# spec\n- R1: changed\n")
        self.assert_problem("gate 2: owner approval is stale")

    def test_finished_change_keeps_its_mode(self):
        self.sign_gate(2)
        self.write_pod_yml()  # the pod switches back to mode: pod
        self.assertEqual(self.check(self.change, "2").returncode, 0)
        res = self.agent_sign(3)
        self.assertEqual(res.returncode, 1)

    def test_agent_lines_rejected_in_pod_mode_without_mode_record(self):
        self.sign_gate(2)
        self.write_pod_yml()
        path = os.path.join(self.change, "gates.log")
        with open(path, encoding="utf-8") as fh:
            kept = [l for l in fh.read().splitlines() if not l.startswith("event=mode")]
        self.write_log(self.change, kept)
        self.assert_problem("gate 2: agent signature not allowed here (mode: pod)")

    def test_full_low_change_through_release(self):
        for gate in (2, 3, 4):
            self.sign_gate(gate)
        res = self.check(self.change)
        self.assertEqual(res.returncode, 0, res.stdout)
        res = self.sh("release-check.sh", self.change)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


# ---------- R12: auto-merge with agent-signed gates ----------

class AutonomousAutoMergeTests(AutoMergeRepo):
    def test_auto_merge_allows_agent_signed_gates(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write(AUTONOMOUS)
        lines = [l for l in self.log_lines(self.c) if l.startswith("gate=1 ")]
        lines.append("event=mode mode=autonomous at=2026-10-10T09:00:00Z")
        usage = []
        for gate, (owner, cross) in ((2, ("superbiz", "superdev")), (3, ("superdev", "superbiz"))):
            b = lib.blob_hash(os.path.join(self.c, lib.ARTIFACTS[gate]))
            for i, (role, leg) in enumerate((("owner", owner), ("cross", cross))):
                model = SONNET if leg == "superbiz" else OPUS
                session = "s%d%d" % (gate, i)
                lines.append("gate=%d role=%s by=agent:%s model=%s session=%s at=2026-10-10T1%d:0%d:00Z blob=%s"
                             % (gate, role, leg, model, session, gate, i, b))
                usage.append("event=usage at=2026-10-10T10:00:00Z session=%s agent=main model=%s input=1 output=1 "
                             "cache_write=0 cache_write_1h=0 cache_read=0 usd=0.01 seconds=1" % (session, model))
        self.write_log(self.c, lines)
        with open(os.path.join(self.c, "activity.log"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(usage) + "\n")
        self.commit("docs(003): agent signatures")
        res = self.auto()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(res.stdout.strip(), "ALLOW")


# ---------- R13: who signed ----------

class VisibilityTests(SeatRepo):
    def test_activity_and_metrics_count_signatures(self):
        self.sign_gate(2)
        out = self.sh("activity.sh", self.change).stdout
        self.assertIn("signatures: people 2, agents 2 (%s 1, %s 1)" % (OPUS, SONNET), out)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "docs: change")
        out = self.sh("metrics.sh", self.change).stdout
        self.assertIn("signatures: people 2, agents 2", out)

    def test_no_signatures_yet(self):
        os.remove(os.path.join(self.change, "gates.log"))
        out = self.sh("activity.sh", self.change).stdout
        self.assertIn("signatures: none yet", out)
