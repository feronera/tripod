"""Tests for scripts/*.sh and plugin hooks, using temporary git repos."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

POD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIZ, DEV, LEAD, OTHER = "biz@example.com", "dev@example.com", "lead@example.com", "x@example.com"
HOOKS_BIZ = os.path.join(POD, "plugins", "superbiz", "hooks")
HOOKS_DEV = os.path.join(POD, "plugins", "superdev", "hooks")
# smallest plan.md that passes the gate 3 structure check
VALID_PLAN = """# plan
## Data shape
dict order_id -> record {customer_id, status, items}
## Throughput checkpoint
- Blocking first steps: failing tests
- Independent workstreams: n/a: one small file
- Shared mutable state: app/orders.py
- Smallest safe decomposition: one requirement per commit
## Parallel parts
none: one file only
"""


def run(cmd, cwd, env=None, stdin=None):
    full_env = dict(os.environ)
    full_env.pop("CLAUDE_PROJECT_DIR", None)
    full_env.update(env or {})
    return subprocess.run(cmd, cwd=cwd, env=full_env, input=stdin,
                          capture_output=True, text=True)


class PodRepo(unittest.TestCase):
    """Base: a fresh temp repo with the pod scripts, templates and pod.yml."""

    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="pod-test-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        shutil.copytree(os.path.join(POD, "scripts"), os.path.join(self.root, "scripts"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(POD, "docs", "templates"),
                        os.path.join(self.root, "docs", "templates"))
        os.makedirs(os.path.join(self.root, "docs", "changes"))
        self.write_pod_yml()
        with open(os.path.join(self.root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("!docs/changes/*/gates.log\n")
        run(["git", "init", "-q"], self.root)
        run(["git", "config", "user.name", "test"], self.root)
        self.as_user(BIZ)

    def write_pod_yml(self, biz=BIZ, dev=DEV, wip=2):
        with open(os.path.join(self.root, "pod.yml"), "w", encoding="utf-8") as fh:
            fh.write("superbiz_name: Biz\nsuperbiz_email: %s\nsuperdev_name: Dev\n"
                     "superdev_email: %s\nescalation_name: Lead\nescalation_email: %s\n"
                     "wip_limit: %d\n" % (biz, dev, LEAD, wip))

    def as_user(self, email):
        run(["git", "config", "user.email", email], self.root)

    def sh(self, name, *args):
        return run([os.path.join(self.root, "scripts", name)] + list(args), self.root)

    def new_change(self, slug="demo", risk="low"):
        res = self.sh("new-change.sh", slug)
        self.assertEqual(res.returncode, 0, res.stderr)
        path = os.path.join(self.root, res.stdout.strip())
        self.assertTrue(os.path.isdir(path), res.stdout)
        if risk != "low":
            self.edit(path, "intent.md", None, risk=risk)
        return path

    def edit(self, change, name, text, risk=None):
        path = os.path.join(change, name)
        if risk is not None:
            with open(path, encoding="utf-8") as fh:
                content = fh.read().replace("Risk: low", "Risk: %s" % risk)
        else:
            content = text
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def approve(self, change, gate, email, expect_ok=True):
        self.as_user(email)
        res = self.sh("gate.sh", change, str(gate))
        if expect_ok:
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res

    def pass_gate(self, change, gate, risk="low"):
        owner, cross = (BIZ, DEV) if gate in (1, 2) else (DEV, BIZ)
        artifact = {1: "intent.md", 2: "spec.md", 3: "plan.md", 4: "acceptance.md"}[gate]
        if not os.path.exists(os.path.join(change, artifact)):
            self.edit(change, artifact, VALID_PLAN if gate == 3 else "# %s\n" % artifact)
        self.approve(change, gate, owner)
        self.approve(change, gate, cross)
        if risk == "high" and gate in (2, 4):
            self.approve(change, gate, LEAD)

    def check(self, *args):
        return self.sh("gate-check.sh", *args)

    def write_log(self, change, lines):
        with open(os.path.join(change, "gates.log"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def blob(self, change, name):
        return run(["git", "hash-object", os.path.join(change, name)], self.root).stdout.strip()


class GateTests(PodRepo):
    def test_owner_and_cross_pass(self):
        c = self.new_change()
        self.pass_gate(c, 1)
        res = self.check(c)
        self.assertEqual(res.returncode, 0, res.stdout)
        with open(os.path.join(c, "gates.log"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r"^gate=1 role=owner by=biz@example.com at=\S+ blob=[0-9a-f]{40}$")
        self.assertIn("role=cross by=dev@example.com", lines[1])
        self.assertTrue(lines[0].endswith(self.blob(c, "intent.md")))

    def test_owner_only_is_incomplete(self):
        c = self.new_change()
        self.approve(c, 1, BIZ)
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("missing cross", res.stdout)

    def test_blob_matches_git_hash_object(self):
        c = self.new_change()
        self.approve(c, 1, BIZ)
        with open(os.path.join(c, "gates.log"), encoding="utf-8") as fh:
            self.assertIn("blob=" + self.blob(c, "intent.md"), fh.read())

    def test_same_person_as_owner_and_cross_fails(self):
        c = self.new_change()
        b = self.blob(c, "intent.md")
        self.write_log(c, ["gate=1 role=owner by=%s at=2026-01-01T09:00:00+07:00 blob=%s" % (BIZ, b),
                           "gate=1 role=cross by=%s at=2026-01-01T09:05:00+07:00 blob=%s" % (BIZ, b)])
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("must differ", res.stdout)

    def test_same_email_for_both_seats_is_refused(self):
        self.write_pod_yml(biz=BIZ, dev=BIZ)
        c = self.new_change()
        res = self.approve(c, 1, BIZ, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(c, "gates.log")))

    def test_unknown_email_is_refused(self):
        c = self.new_change()
        res = self.approve(c, 1, OTHER, expect_ok=False)
        self.assertEqual(res.returncode, 1)

    def test_wrong_role_order_fails(self):
        c = self.new_change()
        # gate.sh refuses cross before owner
        res = self.approve(c, 1, DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("owner", res.stderr)
        # a hand-written log with cross first is rejected by gate-check
        b = self.blob(c, "intent.md")
        self.write_log(c, ["gate=1 role=cross by=%s at=2026-01-01T09:00:00+07:00 blob=%s" % (DEV, b),
                           "gate=1 role=owner by=%s at=2026-01-01T09:05:00+07:00 blob=%s" % (BIZ, b)])
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("wrong role order", res.stdout)

    def test_role_mismatch_fails(self):
        c = self.new_change()
        b = self.blob(c, "intent.md")
        self.write_log(c, ["gate=1 role=owner by=%s at=2026-01-01T09:00:00+07:00 blob=%s" % (DEV, b),
                           "gate=1 role=cross by=%s at=2026-01-01T09:05:00+07:00 blob=%s" % (BIZ, b)])
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("role mismatch", res.stdout)

    def test_gate_without_previous_fails(self):
        c = self.new_change()
        self.edit(c, "spec.md", "# spec\n")
        res = self.approve(c, 2, BIZ, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        b = self.blob(c, "spec.md")
        self.write_log(c, ["gate=2 role=owner by=%s at=2026-01-01T09:00:00+07:00 blob=%s" % (BIZ, b),
                           "gate=2 role=cross by=%s at=2026-01-01T09:05:00+07:00 blob=%s" % (DEV, b)])
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("requires gate 1", res.stdout)

    def test_missing_artifact_is_refused(self):
        c = self.new_change()
        self.pass_gate(c, 1)
        res = self.approve(c, 2, BIZ, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("spec.md", res.stderr)

    def test_stale_approval_fails(self):
        c = self.new_change()
        self.pass_gate(c, 1)
        self.assertEqual(self.check(c).returncode, 0)
        with open(os.path.join(c, "intent.md"), "a", encoding="utf-8") as fh:
            fh.write("\nedited after approval\n")
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("stale", res.stdout)
        # re-approving the new version fixes it
        self.pass_gate(c, 1)
        self.assertEqual(self.check(c).returncode, 0)

    def test_full_flow_low_risk(self):
        c = self.new_change()
        for gate in (1, 2, 3, 4):
            self.pass_gate(c, gate)
        res = self.check(c, "4")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_check_upto_reports_missing_gates(self):
        c = self.new_change()
        self.pass_gate(c, 1)
        self.assertEqual(self.check(c).returncode, 0)
        self.assertEqual(self.check(c, "4").returncode, 1)

    def test_high_risk_needs_escalation_at_2_and_4(self):
        c = self.new_change(risk="high")
        self.pass_gate(c, 1)
        # escalation is not used at gate 1
        res = self.approve(c, 1, LEAD, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.edit(c, "spec.md", "# spec\n")
        self.approve(c, 2, BIZ)
        self.approve(c, 2, DEV)
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("missing escalation", res.stdout)
        # gate 3 cannot start before escalation signs gate 2
        self.edit(c, "plan.md", VALID_PLAN)
        self.assertEqual(self.approve(c, 3, DEV, expect_ok=False).returncode, 1)
        self.approve(c, 2, LEAD)
        self.assertEqual(self.check(c).returncode, 0)
        self.pass_gate(c, 3)
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.approve(c, 4, DEV)
        self.approve(c, 4, BIZ)
        self.assertEqual(self.check(c, "4").returncode, 1)
        self.approve(c, 4, LEAD)
        self.assertEqual(self.check(c, "4").returncode, 0)

    def test_check_all(self):
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)
        draft = self.new_change("draft")
        self.assertEqual(self.check("--all").returncode, 0)
        self.pass_gate(draft, 1)
        self.assertEqual(self.check("--all").returncode, 0)
        with open(os.path.join(draft, "intent.md"), "a", encoding="utf-8") as fh:
            fh.write("changed\n")
        res = self.check("--all")
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL", res.stdout)


class IgnoredLogTests(PodRepo):
    """A global *.log ignore must not silently swallow approvals."""

    def ignore_logs(self):
        with open(os.path.join(self.root, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("")
        with open(os.path.join(self.root, ".git", "info", "exclude"), "a", encoding="utf-8") as fh:
            fh.write("*.log\n")

    def test_gate_refused_when_log_is_ignored(self):
        c = self.new_change()
        self.ignore_logs()
        res = self.sh("gate.sh", c, "1")
        self.assertEqual(res.returncode, 1)
        self.assertIn("gates.log is ignored by git", res.stderr)
        self.assertFalse(os.path.exists(os.path.join(c, "gates.log")))

    def test_gate_check_fails_when_existing_log_is_ignored(self):
        c = self.new_change()
        self.assertEqual(self.sh("gate.sh", c, "1").returncode, 0)
        self.ignore_logs()
        res = self.sh("gate-check.sh", "--all")
        self.assertEqual(res.returncode, 1)
        self.assertIn("gates.log is ignored by git", res.stdout)

    def test_repo_exception_beats_global_ignore(self):
        c = self.new_change()
        with open(os.path.join(self.root, ".git", "info", "exclude"), "a", encoding="utf-8") as fh:
            fh.write("*.log\n")
        self.assertEqual(self.sh("gate.sh", c, "1").returncode, 0)


class NewChangeTests(PodRepo):
    def test_numbering(self):
        first = self.new_change("first")
        second = self.new_change("second")
        self.assertTrue(first.endswith("docs/changes/001-first"))
        self.assertTrue(second.endswith("docs/changes/002-second"))
        self.assertTrue(os.path.exists(os.path.join(second, "intent.md")))

    def test_bad_slug(self):
        self.assertEqual(self.sh("new-change.sh", "Bad Slug").returncode, 2)

    def test_wip_limit_blocks_new_change(self):
        a = self.new_change("a")
        b = self.new_change("b")
        # drafts do not count toward WIP
        self.new_change("c")
        self.pass_gate(a, 1)
        self.pass_gate(b, 1)
        res = self.sh("new-change.sh", "d")
        self.assertEqual(res.returncode, 1)
        self.assertIn("WIP", res.stderr)
        # finishing one change frees a slot
        for gate in (2, 3, 4):
            self.pass_gate(a, gate)
        self.assertEqual(self.sh("new-change.sh", "d").returncode, 0)


class MetricsTests(PodRepo):
    def test_metrics_prints_durations(self):
        c = self.new_change()
        run(["git", "add", "-A"], self.root)
        res = run(["git", "commit", "-q", "-m", "intent"], self.root)
        self.assertEqual(res.returncode, 0, res.stderr)
        for gate in (1, 2, 3, 4):
            self.pass_gate(c, gate)
        res = self.sh("metrics.sh", c)
        self.assertEqual(res.returncode, 0, res.stderr)
        for label in ("intent", "gate 1", "gate 2", "gate 3", "gate 4"):
            self.assertIn(label, res.stdout)
        self.assertRegex(res.stdout, r"gate 4\s+\S+\s+\d+h \d{2}m")
        self.assertRegex(res.stdout, r"lead time intent -> gate 4: \d+h \d{2}m")

    def test_metrics_needs_committed_intent(self):
        c = self.new_change()
        self.assertEqual(self.sh("metrics.sh", c).returncode, 1)


class HookTests(PodRepo):
    def hook(self, path, payload, project=None):
        env = {"CLAUDE_PROJECT_DIR": project or self.root}
        return run([path], self.root, env=env, stdin=json.dumps(payload))

    def write_payload(self, file_path, tool="Write"):
        return {"tool_name": tool, "tool_input": {"file_path": file_path, "content": "x"},
                "cwd": self.root}

    # biz-scope
    def test_biz_scope_allows_docs(self):
        hook = os.path.join(HOOKS_BIZ, "biz-scope.sh")
        for p in ("docs/changes/001-x/intent.md", os.path.join(self.root, "docs", "new.md")):
            res = self.hook(hook, self.write_payload(p))
            self.assertEqual(res.returncode, 0, (p, res.stderr))

    def test_biz_scope_blocks_outside_docs(self):
        hook = os.path.join(HOOKS_BIZ, "biz-scope.sh")
        for p in ("app/orders.py", os.path.join(self.root, "tests", "t.py"),
                  "docs/../app/x.py", "/etc/hosts", "docsx/a.md"):
            res = self.hook(hook, self.write_payload(p, "Edit"))
            self.assertEqual(res.returncode, 2, p)
            self.assertIn("SuperBiz may edit only docs/", res.stderr)

    def test_biz_scope_uses_cwd_without_env(self):
        hook = os.path.join(HOOKS_BIZ, "biz-scope.sh")
        res = run([hook], "/", stdin=json.dumps(self.write_payload("docs/a.md")))
        self.assertEqual(res.returncode, 0, res.stderr)
        res = run([hook], "/", stdin=json.dumps(self.write_payload("app/a.py")))
        self.assertEqual(res.returncode, 2)

    # protect-tests
    def test_protect_tests(self):
        hook = os.path.join(HOOKS_DEV, "protect-tests.sh")
        payload = self.write_payload("tests/test_orders.py", "Edit")
        self.assertEqual(self.hook(hook, payload).returncode, 0)
        os.makedirs(os.path.join(self.root, ".pod"))
        open(os.path.join(self.root, ".pod", "lock-tests"), "w").close()
        res = self.hook(hook, payload)
        self.assertEqual(res.returncode, 2)
        self.assertIn("tests are locked", res.stderr)
        abs_payload = self.write_payload(os.path.join(self.root, "tests", "new_test.py"))
        self.assertEqual(self.hook(hook, abs_payload).returncode, 2)
        self.assertEqual(self.hook(hook, self.write_payload("app/orders.py", "Edit")).returncode, 0)

    # kill-switch
    def test_kill_switch(self):
        hook = os.path.join(HOOKS_DEV, "kill-switch.sh")
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}, "cwd": self.root}
        self.assertEqual(self.hook(hook, payload).returncode, 0)
        os.makedirs(os.path.join(self.root, ".pod"))
        open(os.path.join(self.root, ".pod", "kill-switch"), "w").close()
        res = self.hook(hook, payload)
        self.assertEqual(res.returncode, 2)
        self.assertIn("kill switch is on", res.stderr)

    # gate-guard
    def bash(self, command):
        hook = os.path.join(HOOKS_DEV, "gate-guard.sh")
        return self.hook(hook, {"tool_name": "Bash", "tool_input": {"command": command},
                                "cwd": self.root})

    def test_gate_guard_allows_normal_commands(self):
        for cmd in ("git status", "make test", "git push origin feature/x", "gh pr create"):
            self.assertEqual(self.bash(cmd).returncode, 0, cmd)

    def test_gate_guard_blocks_without_gate_4(self):
        for cmd in ("gh pr merge 3 --squash", "git push origin main", "git push -u origin master",
                    "git checkout main && git merge feature/x"):
            res = self.bash(cmd)
            self.assertEqual(res.returncode, 2, cmd)
        c = self.new_change()
        for gate in (1, 2, 3):
            self.pass_gate(c, gate)
        res = self.bash("gh pr merge 3")
        self.assertEqual(res.returncode, 2)
        self.assertIn("gate 4", res.stderr)

    def test_gate_guard_allows_after_gate_4(self):
        c = self.new_change()
        for gate in (1, 2, 3, 4):
            self.pass_gate(c, gate)
        self.assertEqual(self.bash("gh pr merge 3 --squash").returncode, 0)
        self.assertEqual(self.bash("git push origin main").returncode, 0)
        # a stale approval anywhere blocks again
        with open(os.path.join(c, "plan.md"), "a", encoding="utf-8") as fh:
            fh.write("late edit\n")
        res = self.bash("git push origin main")
        self.assertEqual(res.returncode, 2)
        self.assertIn("stale", res.stderr)


class PluginFilesTests(unittest.TestCase):
    def test_hook_configs_point_to_executable_scripts(self):
        for plugin in ("superbiz", "superdev"):
            base = os.path.join(POD, "plugins", plugin)
            with open(os.path.join(base, "hooks", "hooks.json"), encoding="utf-8") as fh:
                config = json.load(fh)
            for group in config["hooks"]["PreToolUse"]:
                for h in group["hooks"]:
                    path = h["command"].strip('"').replace("${CLAUDE_PLUGIN_ROOT}", base)
                    self.assertTrue(os.access(path, os.X_OK), path)

    def test_scripts_are_executable(self):
        for name in ("new-change.sh", "gate.sh", "gate-check.sh", "metrics.sh", "test-strength.sh",
                     "release-check.sh", "mark-revert.sh", "auto-merge-check.sh", "pr-check.sh",
                     "sync-codeowners.sh", "setup-github.sh"):
            self.assertTrue(os.access(os.path.join(POD, "scripts", name), os.X_OK), name)


if __name__ == "__main__":
    unittest.main()
