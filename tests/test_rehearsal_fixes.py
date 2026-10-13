"""Tests for change 010: fixes from the lab rehearsal. gate.sh says how to share a signature and refuses a repeat
signature; the installer keeps Python's compiled files out of git."""
import os
import shutil
import tempfile

from tests import test_pod_scripts as scripts

REL = "docs/changes/001-demo"


class GateTests(scripts.PodRepo):
    def sign(self, email, gate=1):
        self.as_user(email)
        return self.sh("gate.sh", REL, str(gate))

    def owner_lines(self):
        with open(os.path.join(self.root, REL, "gates.log"), encoding="utf-8") as fh:
            return [l for l in fh.read().splitlines() if "role=owner" in l]

    def test_next_step_after_recording(self):
        self.new_change("demo")
        res = self.sign(scripts.BIZ)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.splitlines()[-1],
                         'Next: share the signature: git add %s/gates.log && git commit -m "gate 1" && git push' % REL)

    def test_repeat_signature_is_refused(self):
        self.new_change("demo")
        self.sign(scripts.BIZ)
        res = self.sign(scripts.BIZ)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: you already signed gate 1 as owner for the current intent.md. The other role must be "
                      "signed by someone else (see docs/gates.md)", res.stderr)
        self.assertEqual(len(self.owner_lines()), 1)

    def test_signing_again_after_a_change_is_allowed(self):
        c = self.new_change("demo")
        self.sign(scripts.BIZ)
        with open(os.path.join(c, "intent.md"), "a", encoding="utf-8") as fh:
            fh.write("\nOne more line.\n")
        res = self.sign(scripts.BIZ)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(len(self.owner_lines()), 2)

    def test_bootstrap_owner_and_escalation_in_one_step(self):
        with open(os.path.join(self.root, "pod.yml"), "w", encoding="utf-8") as fh:
            fh.write("superbiz_name: Biz\nsuperbiz_email: %s\nsuperdev_name: Dev\nsuperdev_email: %s\n"
                     "escalation_name: Biz\nescalation_email: %s\nwip_limit: 2\nbootstrap: on\n"
                     % (scripts.BIZ, scripts.DEV, scripts.BIZ))
        c = self.new_change("demo", risk="high")
        self.sign(scripts.BIZ)
        self.sign(scripts.DEV)
        self.edit(c, "spec.md", "# spec\n")
        res = self.sign(scripts.BIZ, gate=2)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("role=escalation", res.stdout)


class InstallerTests(scripts.PodRepo):
    def install(self, gitignore=None):
        target = os.path.realpath(tempfile.mkdtemp(prefix="pod-target-"))
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        scripts.run(["git", "init", "-q"], target)
        if gitignore is not None:
            with open(os.path.join(target, ".gitignore"), "w", encoding="utf-8") as fh:
                fh.write(gitignore)
        res = scripts.run([os.path.join(scripts.POD, "scripts", "pod-install.sh"), target], target)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        with open(os.path.join(target, ".gitignore"), encoding="utf-8") as fh:
            return fh.read().splitlines()

    def test_pycache_is_ignored(self):
        self.assertIn("__pycache__/", self.install())

    def test_existing_line_is_not_repeated(self):
        self.assertEqual(self.install("__pycache__/\n").count("__pycache__/"), 1)
