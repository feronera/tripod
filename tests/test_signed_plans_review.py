"""Tests added at review for change 007 (approved by the PO while tests/test_signed_plans.py stays locked):
a change cannot name its own branch as the base to skip the plan check, and the base log is parsed like read_log."""
import os

from tests.test_pod_scripts import BIZ, DEV, run
from tests.test_signed_plans import RULE, SignedPlanTests


class ReviewBase(SignedPlanTests):
    """SignedPlanTests' helpers without re-running its tests here."""


for _name in [n for n in dir(SignedPlanTests) if n.startswith("test_")]:
    setattr(ReviewBase, _name, None)


class BaseRedirectTests(ReviewBase):
    def on_own_branch(self, base):
        """The old change committed only on its own branch, whose pod.yml names `base` as the base branch."""
        self.git("checkout", "-q", "-b", "change/001-old")
        c = self.old_change()
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write("base_branch: %s\n" % base)
        self.commit()
        return c

    def test_a_change_branch_is_never_the_base(self):
        c = self.on_own_branch("change/001-old")
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)

    def test_ci_base_ref_must_match(self):
        c = self.on_own_branch("feature-x")
        self.git("branch", "feature-x")  # same commit as the change branch
        res = run([os.path.join(self.root, "scripts", "gate-check.sh"), c], self.root, env={"GITHUB_BASE_REF": "main"})
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)

    def test_ci_base_ref_that_matches_still_allows_the_skip(self):
        c = self.old_change()
        self.commit()
        res = run([os.path.join(self.root, "scripts", "gate-check.sh"), c], self.root, env={"GITHUB_BASE_REF": "main"})
        self.assertEqual(res.returncode, 0, res.stdout)


class BaseLogParsingTests(ReviewBase):
    def test_comments_and_quoted_text_are_not_signatures(self):
        c = self.old_change(roles=("owner",))
        b = self.blob(c)
        with open(os.path.join(c, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("# gate=3 role=cross by=%s blob=%s\n" % (BIZ, b))
            fh.write('event=resume by=%s at=2026-10-01T10:00:00+07:00 reason="gate=3 role=cross blob=%s"\n' % (DEV, b))
        self.commit()
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)
