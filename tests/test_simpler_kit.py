"""Tests for change 009: auto-merge-check compares against the trusted base by default, not a hard-coded main."""
from tests import test_pod_v2 as v2
from tests.test_pod_v2 import git


class DefaultBaseTests(v2.AutoMergeRepo):
    def use_base(self, line):
        """Put `line` in pod.yml on the base too, rename main to trunk, and bring the change up to date."""
        git(self.root, "checkout", "-q", "main")
        self.write("pod.yml", line + "\n", "a")
        self.commit("chore: base branch")
        git(self.root, "branch", "-M", "main", "trunk")
        git(self.root, "checkout", "-q", "change/003")
        git(self.root, "merge", "-q", "--no-edit", "trunk")
        self.write_review(head=self.head())
        self.commit("docs(003): review again")

    def test_default_base_is_base_branch(self):
        self.use_base("base_branch: trunk")
        res = self.sh("auto-merge-check.sh", self.c)
        self.assertEqual((res.returncode, res.stdout.strip()), (0, "ALLOW"), res.stdout)

    def test_explicit_base_still_wins(self):
        self.use_base("base_branch: trunk")
        res = self.sh("auto-merge-check.sh", self.c, "--base", "no-such-branch")
        self.assertEqual(res.returncode, 1)
        self.assertIn("cannot compare with base 'no-such-branch'", res.stdout)

    def test_untrusted_base_is_a_deny_reason(self):
        self.use_base("base_branch: change/003")
        res = self.sh("auto-merge-check.sh", self.c)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout.splitlines()[0], "DENY")
        self.assertIn("base_branch: change/003 is a change branch", res.stdout)
