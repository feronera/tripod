"""Tests added at review for change 004 (approved by the PO while tests/test_loop.py stays locked).
They cover: a branch may change only its own change folder (so it can never change the scripts, plugins or
pod.yml the loop runs), the brief path checked like every step, the kill switch in the middle of a run, a branch
without a change folder, leftovers after checkout, append-only activity.log, and no secrets for agents."""
import os
import sys

from tests.test_loop import SPEC, LoopRepo
from tests.test_pod_scripts import BIZ, DEV, POD
from tests.test_pod_v2 import git

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402

MARK = "PLANTED-RAN"


class BranchRuleTests(LoopRepo):
    def plant(self, script):
        """The branch changes a kit script so that, if it ran, it would leave a marker file."""
        path = os.path.join(self.root, "scripts", script)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\ntouch %s/%s\n" % (self.root, MARK))

    def test_branch_cannot_move_base_branch_or_run_its_own_scripts(self):
        self.loop_sh(FAKE_ACTION=SPEC)  # spec drafted: next is sign gate 2
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("base_branch: change/001-demo\n")
        self.plant("agent-sign.sh")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "tamper")
        res = self.loop_sh()  # run from the tampered branch: its pod.yml names itself as the base
        self.assertEqual(res.returncode, 1)
        self.assertIn("base_branch: change/001-demo is a change branch", res.stdout)
        git(self.root, "checkout", "-q", "main")
        res = self.loop_sh()  # run from the base branch: the pod.yml change is a sensitive path
        self.assertIn("001-demo: stopped: the branch touches a sensitive path (pod.yml, scripts/agent-sign.sh)",
                      res.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.root, MARK)))

    def test_brief_path_is_checked_like_every_step(self):
        self.edit(self.change, "intent.md", None, risk="high")
        b = self.blob(self.change, "intent.md")
        with open(os.path.join(self.change, "gates.log"), "w", encoding="utf-8") as fh:
            fh.write("gate=1 role=owner by=%s at=2026-10-10T00:00:00+00:00 blob=%s\n" % (BIZ, b))
            fh.write("gate=1 role=cross by=%s at=2026-10-10T00:01:00+00:00 blob=%s\n" % (DEV, b))
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "high risk")
        self.loop_sh(FAKE_ACTION=SPEC)
        self.plant("superceo.sh")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "tamper")
        res = self.loop_sh(FAKE_TEXT="## Decision")
        self.assertIn("stopped: the branch touches a sensitive path", res.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.root, MARK)))
        self.assertFalse(os.path.exists(os.path.join(self.change, "brief.md")))

    def test_files_outside_the_own_folder_stop_the_loop(self):
        os.makedirs(os.path.join(self.root, "docs", "notes"), exist_ok=True)
        with open(os.path.join(self.root, "docs", "notes", "idea.md"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "other docs")
        res = self.loop_sh(FAKE_ACTION=SPEC)
        self.assertIn("the branch changes files outside docs/changes/001-demo/ (docs/notes/idea.md)", res.stdout)
        self.assertEqual(self.calls(), [])


class RunTests(LoopRepo):
    def second_change(self, name="002-other"):
        git(self.root, "checkout", "-q", "main")
        git(self.root, "checkout", "-q", "-b", "change/%s" % name)
        folder = os.path.join(self.root, "docs", "changes", name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "intent.md"), "w", encoding="utf-8") as fh:
            fh.write("# Intent: other\n\nRisk: low\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "intent")
        git(self.root, "checkout", "-q", "change/001-demo")

    def test_kill_switch_in_the_middle_of_a_run(self):
        self.second_change()
        action = SPEC + "; mkdir -p .pod; touch .pod/kill-switch"
        res = self.loop_sh(FAKE_ACTION=action)
        self.assertIn("001-demo: draft spec", res.stdout)
        self.assertIn("002-other: stopped: kill switch is on (.pod/kill-switch)", res.stdout)

    def test_branch_without_a_change_folder_is_skipped_and_named(self):
        git(self.root, "checkout", "-q", "main")
        git(self.root, "checkout", "-q", "-b", "change/003-ghost")
        git(self.root, "checkout", "-q", "change/001-demo")
        res = self.loop_sh(FAKE_ACTION=SPEC)
        self.assertIn("003-ghost: skipped: no docs/changes/003-ghost/intent.md on its branch", res.stdout)

    def test_leftovers_after_checkout_are_never_deleted(self):
        git(self.root, "checkout", "-q", "main")
        with open(os.path.join(self.root, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write("local.env\n")
        git(self.root, "commit", "-qam", "ignore local.env")
        with open(os.path.join(self.root, "local.env"), "w", encoding="utf-8") as fh:
            fh.write("KEY=person\n")
        res = self.loop_sh(FAKE_ACTION=SPEC)  # home is main; the change branch does not ignore local.env
        self.assertIn("001-demo: skipped: files left over after checking out the branch (local.env)", res.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.root, "local.env")))
        self.assertEqual(self.calls(), [])

    def test_activity_log_may_only_grow(self):
        with open(os.path.join(self.change, "activity.log"), "w", encoding="utf-8") as fh:
            fh.write("event=usage at=2026-10-10T10:00:00Z session=x agent=main model=m usd=0.10\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "spend")
        res = self.loop_sh(FAKE_ACTION=SPEC + "; : > docs/changes/001-demo/activity.log")
        self.assertIn("activity.log (rewritten, not appended)", res.stdout)


class SecretTests(LoopRepo):
    def test_agent_env_drops_secrets_and_keeps_sign_in(self):
        old = dict(os.environ)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(old)))
        os.environ.update({"AWS_SECRET_ACCESS_KEY": "a", "MY_API_KEY": "b", "DB_PASSWORD": "c", "GH_TOKEN": "d",
                           "SSH_AUTH_SOCK": "e", "ANTHROPIC_API_KEY": "keep", "LANG": "en_US.UTF-8"})
        env = lib.agent_env({"GIT_AUTHOR_NAME": "x"})
        for key in ("AWS_SECRET_ACCESS_KEY", "MY_API_KEY", "DB_PASSWORD", "GH_TOKEN", "SSH_AUTH_SOCK"):
            self.assertNotIn(key, env)
        self.assertEqual((env["ANTHROPIC_API_KEY"], env["LANG"], env["GIT_AUTHOR_NAME"]), ("keep", "en_US.UTF-8", "x"))

    def test_superceo_session_is_isolated(self):
        git(self.root, "checkout", "-q", "main")
        self.ceo = os.path.join(self.root, "scripts", "superceo.sh")
        from tests.test_pod_scripts import run
        run([self.ceo, "priorities"], self.root, env=dict(self.env, FAKE_TEXT="1. x"))
        [call] = self.calls()
        args = call["argv"]
        self.assertEqual(args[args.index("--setting-sources") + 1], "")
        self.assertIn("--strict-mcp-config", args)
        self.assertIsNone(call["gh_token"])
