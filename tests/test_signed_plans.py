"""Tests for change 007: a plan already merged with its gate 3 signatures is not failed by plan rules added later."""
import os
import shutil

from tests.test_changes_across_branches import BranchRepo
from tests.test_pod_scripts import BIZ, DEV, VALID_PLAN

# a plan an older kit accepted: its parallel parts have no `tests:` line, which today's check requires
OLD_PLAN = VALID_PLAN.replace("## Parallel parts\nnone: one file only\n",
                              "## Parallel parts\n### A\nfiles: app/a.py\n### B\nfiles: app/b.py\n")
RULE = "has no `tests:` line"


class SignedPlanTests(BranchRepo):
    def old_change(self, roles=("owner", "cross")):
        """A change at gate 2 with OLD_PLAN signed at gate 3 by `roles`, as an older kit would have recorded it."""
        c = self.new_change("old")
        self.pass_gate(c, 1)
        self.pass_gate(c, 2)
        self.edit(c, "plan.md", OLD_PLAN)
        b = self.blob(c)
        signer = {"owner": DEV, "cross": BIZ}
        with open(os.path.join(c, "gates.log"), "a", encoding="utf-8") as fh:
            for i, role in enumerate(roles):
                fh.write("gate=3 role=%s by=%s at=2026-10-01T09:0%d:00+07:00 blob=%s\n" % (role, signer[role], i, b))
        return c

    def blob(self, c):
        return self.git("hash-object", os.path.join(c, "plan.md")).strip()

    def commit(self, msg="change"):
        self.git("add", "-A")
        self.git("commit", "-qm", msg)

    def test_merged_old_plan_passes(self):
        c = self.old_change()
        self.commit()
        res = self.check(c)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertNotIn(RULE, res.stdout)

    def test_merged_old_plan_passes_on_a_branch_made_from_main(self):
        c = self.old_change()
        self.commit()
        self.git("checkout", "-q", "-b", "chore/kit-update")
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_old_plan_only_on_a_branch_is_checked(self):
        self.git("checkout", "-q", "-b", "change/001-old")
        c = self.old_change()
        self.commit()
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)

    def test_hand_signed_in_the_working_tree_is_checked(self):
        c = self.old_change()
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)

    def test_partial_signature_on_main_is_checked(self):
        c = self.old_change(roles=("owner",))
        self.commit()
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)

    def test_plan_edited_after_merge_is_checked(self):
        c = self.old_change()
        self.commit()
        with open(os.path.join(c, "plan.md"), "a", encoding="utf-8") as fh:
            fh.write("one more line\n")
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)
        self.assertIn("stale", res.stdout)

    def test_gate_sh_still_refuses_to_sign_an_old_plan(self):
        c = self.old_change(roles=("owner",))
        self.commit()
        self.as_user(BIZ)
        res = self.sh("gate.sh", c, "3")
        self.assertEqual(res.returncode, 1)
        self.assertIn("does not follow the required structure", res.stderr)

    def test_without_git_the_plan_is_checked(self):
        c = self.old_change()
        self.commit()
        shutil.rmtree(os.path.join(self.root, ".git"))
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn(RULE, res.stdout)
