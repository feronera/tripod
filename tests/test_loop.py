"""Tests for change 004: the loop driver and the SuperCEO agent."""
import json
import os
import stat
import sys

from tests.test_agent_seats import AUTONOMOUS, OPUS, SONNET, SeatRepo
from tests.test_pod_scripts import POD, VALID_PLAN, run
from tests.test_pod_v2 import git

sys.path.insert(0, os.path.join(POD, "scripts"))
import loop  # noqa: E402

LOOP_ON = AUTONOMOUS + "loop: on\nsuperceo_model: %s\n" % OPUS

# A stand-in for `claude -p`: logs its arguments, runs FAKE_ACTION (a shell snippet) in the repository, and
# prints Claude Code's JSON result. FAKE_RESULT sets the answer text (agent-sign reads a VERDICT from it).
FAKE = r'''#!/usr/bin/env python3
import json, os, subprocess, sys
with open(os.environ["FAKE_LOG"], "a") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\n")
n = sum(1 for _ in open(os.environ["FAKE_LOG"]))
prompt = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else ""
action = os.environ.get("FAKE_ACTION", "")
if action and "VERDICT" not in prompt:
    subprocess.run(action, shell=True, check=False)
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-default"
result = os.environ.get("FAKE_RESULT", "Q1: yes\nVERDICT: APPROVE") if "VERDICT" in prompt else os.environ.get(
    "FAKE_TEXT", "done")
print(json.dumps({"type": "result", "session_id": "s-%d" % n, "result": result, "total_cost_usd": 0.01,
                  "modelUsage": {model: {"inputTokens": 1, "outputTokens": 1, "cacheReadInputTokens": 0,
                                         "cacheCreationInputTokens": 0, "costUSD": 0.01}}}))
'''


def state(**kw):
    base = dict(change="001-demo", risk="low", gate1=True, spec=True, ux_brief=True, gate2=True, plan=True,
                gate3=True, tests=True, build=True, review=True, auto=True, acceptance=True, gate4=True,
                pr_opened=True, refused={})
    base.update(kw)
    return loop.State(**base)


# ---------- R3: the step table (pure) ----------

class StepTableTests(SeatRepo):
    def cfg(self):
        self.set_mode(LOOP_ON)
        return loop.read_pod(self.root)

    def step(self, **kw):
        return loop.next_step(state(**kw), self.cfg())

    def test_each_row(self):
        rows = [
            (dict(gate1=False), ("stop", "people sign gate 1")),
            (dict(spec=False), ("draft", "draft spec")),
            (dict(ux_brief=False), ("draft", "draft spec")),
            (dict(gate2=False), ("sign", "sign gate 2")),
            (dict(gate2=False, refused={2: True}), ("draft", "revise spec")),
            (dict(plan=False), ("draft", "draft plan")),
            (dict(gate3=False), ("sign", "sign gate 3")),
            (dict(gate3=False, refused={3: True}), ("draft", "revise plan")),
            (dict(tests=False), ("build", "write tests")),
            (dict(build=False), ("build", "build")),
            (dict(review=False), ("build", "review")),
            (dict(auto=False), ("merge", "auto-merge record")),
            (dict(acceptance=False), ("draft", "draft acceptance")),
            (dict(gate4=False), ("sign", "sign gate 4")),
            (dict(gate4=False, refused={4: True}), ("stop", "people decide gate 4 (agents refused it)")),
            (dict(pr_opened=False), ("merge", "open PR")),
            (dict(), ("stop", "done")),
        ]
        for kw, (kind, name) in rows:
            s = self.step(**kw)
            self.assertEqual((s.kind, s.name), (kind, name), kw)

    def test_earlier_rows_win(self):
        self.assertEqual(self.step(spec=False, plan=False, tests=False).name, "draft spec")

    def test_actors(self):
        self.assertEqual(self.step(spec=False).actor, "superbiz")
        self.assertEqual(self.step(plan=False).actor, "superdev")
        self.assertEqual(self.step(build=False).actor, "superdev")
        self.assertEqual(self.step(acceptance=False).actor, "superbiz")
        self.assertEqual(self.step(gate1=False).actor, "people")
        self.assertEqual(self.step().actor, "nobody")

    def test_medium_and_high_stop_for_people(self):
        for risk in ("medium", "high"):
            self.assertEqual(self.step(risk=risk, gate2=False).name, "people sign gate 2 (Risk: %s)" % risk)
            self.assertEqual(self.step(risk=risk, gate3=False).name, "people sign gate 3 (Risk: %s)" % risk)
            self.assertEqual(self.step(risk=risk, auto=False).name, "people merge (Risk: %s)" % risk)
            self.assertEqual(self.step(risk=risk, spec=False).name, "draft spec")  # drafting still happens
            self.assertEqual(self.step(risk=risk, build=False).name, "build")


# ---------- R1, R2: configuration and refusals to start ----------

class LoopRepo(SeatRepo):
    def setUp(self):
        super().setUp()
        with open(os.path.join(self.root, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write("__pycache__/\n.fakebin/\n")
        self.set_mode(LOOP_ON)
        for name in ("superbiz", "superdev", "superceo"):
            src = os.path.join(POD, "plugins", name)
            if os.path.isdir(src):
                git(self.root, "status")  # no-op; plugins are found through TRIPOD_PLUGIN_DIR
        self.fake_log = os.path.join(self.root, ".fakebin", "calls.log")
        with open(self.fake, "w", encoding="utf-8") as fh:
            fh.write(FAKE)
        os.chmod(self.fake, os.stat(self.fake).st_mode | stat.S_IEXEC)
        self.env.update({"FAKE_LOG": self.fake_log, "TRIPOD_PLUGIN_DIR": os.path.join(POD, "plugins"),
                         "TRIPOD_GH": os.path.join(self.root, "no-gh")})
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "change so far")
        git(self.root, "branch", "-f", "main", "HEAD")

    def loop_sh(self, *args, **env):
        full = dict(self.env)
        full.update(env)
        return run([os.path.join(self.root, "scripts", "loop.sh")] + list(args), self.root, env=full)

    def fake_calls(self):
        if not os.path.exists(self.fake_log):
            return []
        with open(self.fake_log, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh]

    def records(self):
        path = os.path.join(self.change, "activity.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return [l for l in fh.read().splitlines() if l.startswith("event=loop")]


class StartTests(LoopRepo):
    def test_off_by_default(self):
        self.set_mode(AUTONOMOUS)
        git(self.root, "commit", "-qam", "loop off")
        res = self.loop_sh()
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: pod.yml sets loop: off. The sponsor turns the loop on with loop: on", res.stdout)

    def test_pod_mode(self):
        self.write_pod_yml()
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("loop: on\n")
        git(self.root, "commit", "-qam", "pod mode")
        self.assertIn("Refused: the loop runs only in mode: autonomous", self.loop_sh().stdout)

    def test_kill_switch(self):
        os.makedirs(os.path.join(self.root, ".pod"), exist_ok=True)
        open(os.path.join(self.root, ".pod", "kill-switch"), "w").close()
        self.assertIn("Refused: kill switch is on (.pod/kill-switch)", self.loop_sh().stdout)

    def test_dirty_tree(self):
        with open(os.path.join(self.root, "README.txt"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        self.assertIn("Refused: the working tree has uncommitted changes; commit or stash them first",
                      self.loop_sh().stdout)

    def test_lock(self):
        os.makedirs(os.path.join(self.root, ".pod"), exist_ok=True)
        with open(os.path.join(self.root, ".pod", "loop.lock"), "w", encoding="utf-8") as fh:
            fh.write("2026-10-10T00:00:00+00:00\n")
        self.assertIn("Refused: another loop run holds .pod/loop.lock (started", self.loop_sh().stdout)

    def test_malformed_keys(self):
        self.set_mode(LOOP_ON + "loop_pace_low: sprint\nloop_max_steps: many\n")
        git(self.root, "commit", "-qam", "bad keys")
        res = self.check("--all")
        self.assertEqual(res.returncode, 1)
        self.assertIn("pod.yml: loop_pace_low: sprint is not step or until-blocked", res.stdout)
        self.assertIn("pod.yml: loop_max_steps: many is not a number", res.stdout)
        self.assertEqual(self.loop_sh().returncode, 1)

    def test_nothing_to_do(self):
        res = self.loop_sh()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("001-demo", res.stdout)  # gate 1 done: the change is open


# ---------- R10: dry run ----------

class DryRunTests(LoopRepo):
    def test_dry_run_changes_nothing(self):
        before = git(self.root, "rev-parse", "HEAD")
        res = self.loop_sh("--dry-run")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("001-demo (low): next: sign gate 2 (agent:superbiz)", res.stdout)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.fake_calls(), [])
        self.assertEqual(git(self.root, "status", "--porcelain"), "")


# ---------- R4, R5, R9: steps, commits and records ----------

class StepRunTests(LoopRepo):
    def test_draft_step_commits_as_the_loop(self):
        os.remove(os.path.join(self.change, "spec.md"))
        git(self.root, "commit", "-qam", "no spec yet")
        action = "printf '# spec\\n- R1: x\\n' > docs/changes/001-demo/spec.md; printf '# ux\\n' > docs/changes/001-demo/ux-brief.md"
        res = self.loop_sh(FAKE_ACTION=action)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("001-demo: draft spec", res.stdout)
        log = git(self.root, "log", "--format=%an <%ae>|%s", "-3")
        self.assertIn("Tripod loop <loop@tripod.invalid>|loop(001): draft spec", log)
        [args] = [a for a in self.fake_calls() if "VERDICT" not in a[a.index("-p") + 1]][:1]
        self.assertEqual(args[args.index("--model") + 1], SONNET)
        self.assertIn("--plugin-dir", args)
        self.assertTrue(args[args.index("--plugin-dir") + 1].endswith(os.path.join("plugins", "superbiz")))
        allowed = args[args.index("--allowedTools") + 1]
        self.assertIn("Write(docs/changes/001-demo/**)", allowed)
        self.assertNotIn("Bash", allowed)
        self.assertTrue(any("step=" in r and "draft spec" in r for r in self.records()))

    def test_sign_step_uses_agent_sign(self):
        res = self.loop_sh()
        self.assertIn("001-demo: sign gate 2 owner → APPROVE", res.stdout)
        with open(os.path.join(self.change, "gates.log"), encoding="utf-8") as fh:
            self.assertIn("by=agent:superbiz", fh.read())

    def test_refusal_stops_the_change(self):
        res = self.loop_sh(FAKE_RESULT="R1 is vague\nVERDICT: REFUSE")
        self.assertIn("001-demo: stopped: sign gate 2 refused", res.stdout)
        self.assertTrue(any("result=refused" in r for r in self.records()))

    def test_failed_step_commits_nothing(self):
        os.remove(os.path.join(self.change, "spec.md"))
        git(self.root, "commit", "-qam", "no spec yet")
        head = git(self.root, "rev-parse", "HEAD")
        res = self.loop_sh(FAKE_ACTION="exit 0")  # the agent wrote nothing
        self.assertIn("001-demo: stopped: draft spec failed", res.stdout)
        self.assertEqual(git(self.root, "log", "--format=%s", "-1"), "loop(001): stopped")  # only the record
        self.assertEqual(git(self.root, "rev-parse", "HEAD~1"), head)

    def test_missing_branch_stops(self):
        git(self.root, "checkout", "-q", "-b", "elsewhere")
        git(self.root, "branch", "-D", "change/001-demo")
        res = self.loop_sh()
        self.assertNotIn("sign gate 2", res.stdout)


# ---------- R6: pace and cap ----------

class PaceTests(LoopRepo):
    def test_step_pace_takes_one_step(self):
        res = self.loop_sh()
        self.assertEqual(res.stdout.count("→ APPROVE"), 1, res.stdout)

    def test_until_blocked_continues(self):
        self.set_mode(LOOP_ON + "loop_pace_low: until-blocked\n")
        git(self.root, "commit", "-qam", "pace")
        res = self.loop_sh()
        self.assertGreaterEqual(res.stdout.count("→ APPROVE"), 2, res.stdout)

    def test_cap(self):
        self.set_mode(LOOP_ON + "loop_pace_low: until-blocked\nloop_max_steps: 1\n")
        git(self.root, "commit", "-qam", "cap")
        res = self.loop_sh()
        self.assertEqual(res.stdout.count("→ APPROVE"), 1, res.stdout)
        self.assertIn("loop_max_steps", res.stdout)


# ---------- R7, R8: limits and what the loop never does ----------

class SafetyTests(LoopRepo):
    def test_limits_stop_the_loop(self):
        self.set_mode(LOOP_ON + "budget_per_change_usd: 0.00\n")
        git(self.root, "commit", "-qam", "budget")
        with open(os.path.join(self.change, "activity.log"), "a", encoding="utf-8") as fh:
            fh.write("event=usage at=2026-10-10T10:00:00Z session=x agent=main model=%s usd=0.50\n" % OPUS)
        git(self.root, "commit", "-qam", "spend")
        res = self.loop_sh()
        self.assertIn("001-demo: stopped: budget for 001-demo reached", res.stdout)
        self.assertEqual([c for c in self.fake_calls()], [])

    def test_never_runs_people_commands(self):
        with open(os.path.join(POD, "scripts", "loop.py"), encoding="utf-8") as fh:
            source = fh.read()
        for name in ("gate.sh", "resume.sh", "mark-revert.sh"):
            self.assertNotIn(name, source.replace("never run", ""))


# ---------- R11-R14: SuperCEO ----------

class SuperCeoTests(LoopRepo):
    def ceo(self, *args, **env):
        full = dict(self.env)
        full.update(env)
        return run([os.path.join(self.root, "scripts", "superceo.sh")] + list(args), self.root, env=full)

    def test_priorities_file(self):
        res = self.ceo("priorities", FAKE_TEXT="1. 001-demo: next sign gate 2 (cheap, unblocks the rest)",
                       TRIPOD_NOW="2026-10-10T12:00:00+00:00")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        path = os.path.join(self.root, "docs", "superceo", "2026-10-10.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("001-demo", text)
        [args] = self.fake_calls()
        self.assertEqual(args[args.index("--model") + 1], OPUS)
        self.assertEqual(args[args.index("--tools") + 1], "Read,Grep,Glob")

    def test_brief_refuses_low_risk(self):
        res = self.ceo("brief", self.change)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: 001-demo is Risk: low; briefs are for decisions people make", res.stdout)

    def test_brief_for_high_risk(self):
        self.edit(self.change, "intent.md", None, risk="high")
        res = self.ceo("brief", self.change, FAKE_TEXT="## Decision\nApprove the spec?\n## Options\n- yes\n- no")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        with open(os.path.join(self.change, "brief.md"), encoding="utf-8") as fh:
            self.assertIn("## Decision", fh.read())

    def test_plugin_and_marketplace(self):
        for path in ("plugins/superceo/.claude-plugin/plugin.json", "plugins/superceo/skills/priorities/SKILL.md",
                     "plugins/superceo/skills/brief/SKILL.md", "plugins/superceo/agents/superceo.md"):
            self.assertTrue(os.path.exists(os.path.join(POD, path)), path)
        with open(os.path.join(POD, ".claude-plugin", "marketplace.json"), encoding="utf-8") as fh:
            self.assertIn("superceo", [p["name"] for p in json.load(fh)["plugins"]])


# ---------- R9, R15: digest and CI ----------

class DigestAndCiTests(LoopRepo):
    def test_digest_section(self):
        self.loop_sh()
        res = run([os.path.join(self.root, "scripts", "digest.sh")], self.root, env=self.env)
        self.assertIn("loop runs: 1 steps", res.stdout)

    def test_ci_template(self):
        with open(os.path.join(POD, "docs", "templates", "loop.yml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("schedule:", text)
        self.assertIn("scripts/loop.sh", text)
        self.assertIn("secrets.ANTHROPIC_API_KEY", text)
        self.assertIn("scripts/digest.sh --write", text)
