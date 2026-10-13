"""Tests for change 011: gate 4 and release-check read the change's own review.md and acceptance.md."""
import os

from tests import test_pod_scripts as scripts

READY_REVIEW = "blockers: 0\nmajors_open: 0\nsecond_opinion: agree\nreviewed_head: x\n\n# Review\n"
ACCEPT = "# Acceptance\n\n## Decision\nDecision: accept\n"


class Gate4Tests(scripts.PodRepo):
    def ready(self, review=READY_REVIEW, acceptance=ACCEPT):
        c = self.new_change("demo")
        for gate in (1, 2, 3):
            self.pass_gate(c, gate)
        if review is not None:
            self.edit(c, "review.md", review)
        self.edit(c, "acceptance.md", acceptance)
        return c

    def gate4_lines(self, c):
        with open(os.path.join(c, "gates.log"), encoding="utf-8") as fh:
            return [l for l in fh if l.startswith("gate=4")]

    def test_blockers_refuse_gate4(self):
        c = self.ready(review=READY_REVIEW.replace("blockers: 0", "blockers: 1"))
        res = self.approve(c, 4, scripts.DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: gate 4 cannot be signed while the change's own artifacts say it is not ready:",
                      res.stderr)
        self.assertIn("  - review.md has blockers: 1", res.stderr)
        self.assertEqual(self.gate4_lines(c), [])

    def test_reject_refuses_gate4_in_any_case(self):
        c = self.ready(acceptance=ACCEPT.replace("Decision: accept", "decision: REJECT"))
        res = self.approve(c, 4, scripts.DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - acceptance.md decides reject", res.stderr)

    def test_ready_change_signs(self):
        c = self.ready()
        self.approve(c, 4, scripts.DEV)
        self.approve(c, 4, scripts.BIZ)
        self.assertEqual(len(self.gate4_lines(c)), 2)

    def test_no_review_and_template_decision_line_still_sign(self):
        c = self.ready(review=None, acceptance="# Acceptance\n\nDecision: accept | reject\n")
        self.approve(c, 4, scripts.DEV)

    def test_release_check_reports_the_reasons(self):
        c = self.ready()
        self.approve(c, 4, scripts.DEV)
        self.approve(c, 4, scripts.BIZ)
        self.edit(c, "review.md", READY_REVIEW.replace("blockers: 0", "blockers: 2"))
        res = self.sh("release-check.sh", c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("NOT RELEASE-READY", res.stdout)
        self.assertIn("review.md has blockers: 2", res.stdout)
