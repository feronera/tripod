"""Tests for bootstrap mode: escalation may share a person with one other role while a pod is small."""
import os
import sys

from tests.test_pod_multi import BEE, DAN, LEE, MultiRepo, pod_text
from tests.test_pod_scripts import POD

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402

BEE_ESC = ("Bee", "bee@pod.example", "bee-gh")


class BootstrapRepo(MultiRepo):
    def setUp(self):
        super().setUp()
        self.set_people(devs=(DAN,), escs=(BEE_ESC,), extra="bootstrap: on\n")


class BootstrapConfigTests(BootstrapRepo):
    def test_escalation_shared_with_superbiz_warns_only(self):
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("Warning: " + lib.BOOTSTRAP_WARNING % "bee@pod.example", res.stdout)

    def test_off_by_default_so_sharing_is_an_error(self):
        self.set_people(devs=(DAN,), escs=(BEE_ESC,))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("email bee@pod.example appears in more than one role (SuperBiz, escalation)", res.stdout)

    def test_superbiz_and_superdev_never_shared(self):
        self.set_people(devs=(("Bee", "bee@pod.example", "bee-gh"),), escs=(LEE,), extra="bootstrap: on\n")
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("appears in more than one role (SuperBiz, SuperDev)", res.stdout)

    def test_unused_bootstrap_warns(self):
        self.set_people(devs=(DAN,), escs=(LEE,), extra="bootstrap: on\n")
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("Warning: " + lib.BOOTSTRAP_UNUSED, res.stdout)

    def test_template_is_off(self):
        cfg = lib.read_pod_yml(os.path.join(POD, "docs", "templates"))
        self.assertFalse(lib.bootstrap_on(cfg))


class BootstrapGateTests(BootstrapRepo):
    def test_high_risk_escalation_recorded_with_superbiz(self):
        c = self.new_change(risk="high")
        self.sign(c, 1, BEE)
        self.sign(c, 1, DAN)
        self.edit(c, "spec.md", "# spec\n")
        res = self.sign(c, 2, BEE)
        self.assertIn("Recorded: gate 2 role=owner by=bee@pod.example", res.stdout)
        self.assertIn("Recorded: gate 2 role=escalation by=bee@pod.example (bootstrap", res.stdout)
        self.assertTrue(self.log_lines(c)[-1].endswith("note=bootstrap"))
        self.sign(c, 2, DAN)
        res = self.check(c)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_low_risk_records_no_escalation(self):
        c = self.new_change()
        self.sign(c, 1, BEE)
        self.sign(c, 1, DAN)
        self.edit(c, "spec.md", "# spec\n")
        self.sign(c, 2, BEE)
        self.assertFalse(any("role=escalation" in l for l in self.log_lines(c)))


class BootstrapPrCheckTests(BootstrapRepo):
    def pr(self, author, approvals=""):
        return self.sh("pr-check.sh", "--author", author, "--approvals", approvals, "--base", "main")

    def test_one_approval_counts_for_superbiz_and_escalation(self):
        self.branch_off_main()
        self.write("app/payment.py", "def pay():\n    return 0\n")
        self.commit(DAN, "feat: pay")
        res = self.pr("dan-gh", "bee-gh")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("PR-CHECK OK (effective Risk: high)", res.stdout)
        self.assertIn("note: bootstrap mode", res.stdout)
        res = self.pr("dan-gh", "")
        self.assertIn("SuperBiz (bee-gh)", res.stdout)
        self.assertIn("escalation (bee-gh)", res.stdout)
