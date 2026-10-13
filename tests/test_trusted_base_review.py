"""Tests added at review for change 008 (approved by the PO while tests/test_trusted_base.py stays locked):
spellings of a change branch are refused, odd names are not plain branch names, and the kit's tests run as
outside CI."""
import os
import sys
import unittest

from tests import test_pod_scripts as scripts
from tests import test_trusted_base as trusted

sys.path.insert(0, os.path.join(scripts.POD, "scripts"))
import lib  # noqa: E402


class VariantTests(unittest.TestCase):
    def problem(self, name, **env):
        trusted.Env(self, **env)
        return lib.base_problem({"base_branch": name})

    def test_spellings_of_a_change_branch_are_refused(self):
        for name in ("refs/heads/change/009-x", "heads/change/009-x", "./change/009-x", "Change/009-x",
                     "refs/remotes/origin/change/009-x", "remotes/origin/change/009-x"):
            self.assertIn("is a change branch", self.problem(name) or "", name)

    def test_names_that_are_not_plain_branches_are_refused(self):
        for name in ("@", "HEAD", "main..x", "-main", "/main", "main@{1}", "ma in"):
            self.assertIn("is not a plain branch name", self.problem(name) or "", name)

    def test_full_ref_of_the_right_branch_matches_ci(self):
        self.assertIsNone(self.problem("refs/heads/main", GITHUB_BASE_REF="main"))

    def test_plain_names_are_fine(self):
        for name in ("main", "develop", "release/1.0", "trunk_2"):
            self.assertIsNone(self.problem(name), name)


class IsolationTests(unittest.TestCase):
    def test_kit_tests_run_as_outside_ci(self):
        code = "import os, tests; print(os.environ.get('GITHUB_BASE_REF'), os.environ.get('GITHUB_EVENT_PATH'))"
        res = scripts.run([sys.executable, "-c", code], scripts.POD,
                          env={"GITHUB_BASE_REF": "develop", "GITHUB_EVENT_PATH": "/tmp/event.json"})
        self.assertEqual(res.stdout.strip(), "None None", res.stderr)
