"""Tests for change 008: one trusted base branch. A change cannot point base_branch at its own branch to hide
from agent-sign, peer review or the mode record, and in CI the pull request's real base wins over pod.yml."""
import json
import os
import sys
import tempfile
import unittest

from tests import test_agent_seats as seats
from tests import test_agent_seats_review as seats_review
from tests import test_pod_multi as multi
from tests import test_pod_scripts as scripts
from tests.test_pod_v2 import git

sys.path.insert(0, os.path.join(scripts.POD, "scripts"))
import lib  # noqa: E402

CHANGE_BASE = "base_branch: change/001-demo is a change branch"


class Env:
    """Set CI variables for one test and restore them afterwards."""

    def __init__(self, test, **values):
        old = {k: os.environ.get(k) for k in ("GITHUB_BASE_REF", "GITHUB_EVENT_PATH")}
        for k in old:
            os.environ.pop(k, None)
        os.environ.update(values)

        def restore():
            for k, v in old.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v
        test.addCleanup(restore)


class BaseProblemTests(unittest.TestCase):
    def problem(self, name, **env):
        Env(self, **env)
        return lib.base_problem({"base_branch": name})

    def test_a_change_branch_is_refused(self):
        self.assertEqual(self.problem("change/001-demo"),
                         CHANGE_BASE + "; the base must be the shared branch changes merge into "
                         "(pod.yml base_branch, default main)")

    def test_an_origin_change_branch_is_refused(self):
        self.assertIn("base_branch: origin/change/001-demo is a change branch", self.problem("origin/change/001-demo"))

    def test_main_is_fine_locally(self):
        self.assertIsNone(self.problem("main"))

    def test_ci_base_must_match(self):
        self.assertEqual(self.problem("develop", GITHUB_BASE_REF="main"),
                         "base_branch: develop does not match the pull request's base branch main")
        self.assertIsNone(self.problem("main", GITHUB_BASE_REF="main"))

    def test_ci_event_payload_is_read(self):
        path = os.path.join(tempfile.mkdtemp(), "event.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"review": {}, "pull_request": {"base": {"ref": "main"}}}, fh)
        self.assertIn("does not match the pull request's base branch main",
                      self.problem("develop", GITHUB_EVENT_PATH=path))

    def test_push_event_uses_pod_yml(self):
        self.assertIsNone(self.problem("main", GITHUB_BASE_REF=""))


class ResolveBaseTests(scripts.PodRepo):
    def test_ci_base_wins_over_pod_yml(self):
        Env(self, GITHUB_BASE_REF="main")
        self.assertEqual(lib.resolve_base("change/001-demo", self.root), "main")

    def test_outside_ci_unchanged(self):
        Env(self)
        self.assertEqual(lib.resolve_base("trunk", self.root), "trunk")


class ConfigTests(scripts.PodRepo):
    def test_gate_check_all_fails(self):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("base_branch: change/001-demo\n")
        res = self.check("--all")
        self.assertEqual(res.returncode, 1)
        self.assertIn(CHANGE_BASE, res.stdout)


class AgentSignTests(seats.SeatRepo):
    def test_agent_sign_refuses_before_starting_an_agent(self):
        self.set_mode(seats.AUTONOMOUS + "base_branch: change/001-demo\n")
        res = self.agent_sign(2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("pod.yml has problems", res.stdout + res.stderr)
        self.assertIn(CHANGE_BASE, res.stdout + res.stderr)
        self.assertEqual(self.calls(), [])


class ModeRecordTests(seats_review.ReviewRepo):
    def test_record_on_a_redirected_base_does_not_count(self):
        self.write_pod_yml()  # Pod mode
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("base_branch: change/001-demo\n")
        self.forge_gate2()
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "forged on the branch")
        res = self.check(self.change, "2")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("agent signature not allowed here (mode: pod)", res.stdout)


class PeerReviewTests(multi.MultiRepo):
    def ready(self, devs=None):
        if devs:
            self.set_people(devs=devs, extra="base_branch: change/001\n")
        else:
            self.set_people(extra="base_branch: change/001\n")
        self.branch_off_main()
        c = self.new_change()
        self.to_gate3(c)
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.commit(multi.BEE, "docs(001): artifacts")
        self.write("app/x.py", "X = 1\n")
        self.commit(multi.DAN, "feat: x")
        return c

    def test_code_author_cannot_hide_behind_a_redirected_base(self):
        c = self.ready()
        res = self.sign(c, 4, multi.DAN, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: peer review cannot be checked: base_branch: change/001 is a change branch",
                      res.stderr)
        self.assertFalse(any("gate=4" in l for l in self.log_lines(c)))

    def test_single_superdev_is_not_refused(self):
        c = self.ready(devs=(multi.DAN,))
        res = self.sign(c, 4, multi.DAN)
        self.assertNotIn("peer review", res.stdout + res.stderr)
