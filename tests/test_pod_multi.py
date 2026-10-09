"""Tests for 0.6.0: several people per role, peer review at gate 4, and pr-check with seat sets."""
import os
import sys
import unittest

from tests.test_pod_scripts import BIZ, DEV, POD, VALID_PLAN, run
from tests.test_pod_v2 import CHECKPOINT, PLAN_HEAD, V2Repo, git
from tests.test_pod_v3 import INSTALL, TempRepo

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402

BEE = ("Bee", "bee@pod.example", "bee-gh")
BO = ("Bo", "bo@pod.example", "bo-gh")
DAN = ("Dan", "dan@pod.example", "dan-gh")
EVE = ("Eve", "eve@pod.example", "eve-gh")
LEE = ("Lee", "lee@pod.example", "lee-gh")


def pod_text(bizs=(BEE,), devs=(DAN, EVE), escs=(LEE,), extra=""):
    lines = []
    for role, people in (("superbiz", bizs), ("superdev", devs), ("escalation", escs)):
        for i, field in enumerate(("name", "email", "github")):
            lines.append("%s_%s: %s" % (role, field, ", ".join(p[i] for p in people)))
    return "\n".join(lines) + "\nwip_limit: 5\n" + extra


class MultiRepo(V2Repo):
    """A temp pod repo whose pod.yml has one SuperBiz, two SuperDevs and one escalation by default."""

    def setUp(self):
        super().setUp()
        self.set_people()

    def set_people(self, **kw):
        self.write("pod.yml", pod_text(**kw))

    def sign(self, change, gate, person, expect_ok=True):
        return self.approve(change, gate, person[1], expect_ok)

    def to_gate3(self, change, owners=((BEE, DAN), (BEE, DAN), (DAN, BEE))):
        for gate, (owner, cross) in enumerate(owners, 1):
            name = lib.ARTIFACTS[gate]
            if not os.path.exists(os.path.join(change, name)):
                self.edit(change, name, VALID_PLAN if gate == 3 else "# %s\n" % name)
            self.sign(change, gate, owner)
            self.sign(change, gate, cross)

    def commit(self, person, msg):
        self.as_user(person[1])
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", msg)

    def branch_off_main(self):
        """main with one base commit, then branch change/001."""
        self.write("app/__init__.py", "")
        self.commit(BEE, "base")
        git(self.root, "branch", "-M", "main")
        git(self.root, "checkout", "-q", "-b", "change/001")


# ---------- pod.yml lists and validation ----------

class ConfigTests(MultiRepo):
    def cfg(self):
        return lib.read_pod_yml(self.root)

    def test_list_parsing(self):
        self.write("pod.yml", pod_text().replace("dan@pod.example", "Dan@Pod.Example").replace("dan-gh", "@dan-gh"))
        cfg = self.cfg()
        self.assertEqual(lib.members(cfg, "superdev"), [
            {"name": "Dan", "email": "dan@pod.example", "github": "dan-gh"},
            {"name": "Eve", "email": "eve@pod.example", "github": "eve-gh"}])
        self.assertEqual(lib.role_emails(cfg, "superbiz"), ["bee@pod.example"])
        self.assertEqual(lib.roles_of_email(cfg, "EVE@pod.example"), ["superdev"])

    def test_single_values_unchanged(self):
        cfg = lib.read_pod_yml(os.path.join(POD, "docs", "templates"))
        self.assertEqual(cfg["superdev_email"], "dev@example.com")
        self.assertEqual(cfg["superbiz_github"], "biz-example")
        self.assertEqual(cfg["base_branch"], "main")
        self.assertEqual(lib.members(cfg, "superdev"),
                         [{"name": "SuperDev Example", "email": "dev@example.com", "github": "dev-example"}])
        self.assertEqual(lib.pod_config_problems(cfg), ([], []))

    def test_mismatched_list_lengths_error(self):
        self.write("pod.yml", pod_text().replace("superdev_github: dan-gh, eve-gh", "superdev_github: dan-gh"))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("FAIL pod.yml", res.stdout)
        self.assertIn("the SuperDev lists have different lengths (superdev_name: 2, superdev_email: 2, "
                      "superdev_github: 1)", res.stdout)

    def test_github_list_may_be_omitted(self):
        self.write("pod.yml", pod_text().replace("superdev_github: dan-gh, eve-gh\n", ""))
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_same_email_or_login_in_two_roles_error(self):
        self.set_people(devs=(DAN, ("Bee", "bee@pod.example", "eve-gh")))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("email bee@pod.example appears in more than one role (SuperBiz, SuperDev)", res.stdout)
        self.set_people(escs=(("Lee", "lee@pod.example", "dan-gh"),))
        res = self.check("--all")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("GitHub login dan-gh appears in more than one role (SuperDev, escalation)", res.stdout)

    def test_more_than_three_superdevs_per_superbiz_warns(self):
        devs = tuple(("D%d" % i, "d%d@pod.example" % i, "d%d-gh" % i) for i in range(4))
        self.set_people(devs=devs)
        res = self.check("--all")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("Warning: " + lib.SCALING_WARNING, res.stdout)
        self.set_people(bizs=(BEE, BO), devs=devs)
        self.assertNotIn("Warning", self.check("--all").stdout)


# ---------- gates with several people per role ----------

class MultiGateTests(MultiRepo):
    def test_any_member_signs_for_their_role(self):
        self.set_people(bizs=(BEE, BO))
        c = self.new_change()
        self.to_gate3(c, owners=((BO, EVE), (BEE, DAN), (EVE, BO)))
        self.edit(c, "acceptance.md", "# acceptance\n")
        res = self.sign(c, 4, DAN)
        self.assertIn("note: peer review skipped: no merge base", res.stdout)
        self.sign(c, 4, BEE)
        res = self.check(c)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(self.sh("release-check.sh", c).returncode, 0)

    def test_owner_and_cross_still_differ_and_unknown_refused(self):
        c = self.new_change()
        self.assertEqual(self.approve(c, 1, "x@pod.example", expect_ok=False).returncode, 1)
        b = self.blob(c, "intent.md")
        self.write_log(c, ["gate=1 role=owner by=bee@pod.example at=2026-01-01T09:00:00+07:00 blob=%s" % b,
                           "gate=1 role=cross by=zed@pod.example at=2026-01-01T09:05:00+07:00 blob=%s" % b])
        res = self.check(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("does not match pod.yml (dan@pod.example, eve@pod.example) (role mismatch)", res.stdout)

    def test_email_in_two_roles_cannot_sign(self):
        self.set_people(devs=(DAN, ("Bee", "bee@pod.example", "x-gh")))
        c = self.new_change()
        res = self.sign(c, 1, BEE, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("more than one role", res.stderr)


# ---------- peer review at gate 4 ----------

class PeerReviewTests(MultiRepo):
    def ready_for_gate4(self):
        self.branch_off_main()
        c = self.new_change()
        self.to_gate3(c)
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.commit(BEE, "docs(001): artifacts")
        return c

    def test_code_author_refused_other_superdev_accepted(self):
        c = self.ready_for_gate4()
        self.write("app/x.py", "X = 1\n")
        self.commit(DAN, "feat: x")
        res = self.sign(c, 4, DAN, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Refused: peer review", res.stderr)
        self.assertIn("authored by: dan@pod.example", res.stderr)
        self.assertIn("Ask another SuperDev to sign gate 4: eve@pod.example", res.stderr)
        self.assertFalse(any("gate=4" in l for l in self.log_lines(c)))
        res = self.sign(c, 4, EVE)
        self.assertIn("Recorded: gate 4 role=owner by=eve@pod.example", res.stdout)

    def test_docs_only_commits_do_not_count(self):
        c = self.ready_for_gate4()
        self.write("app/x.py", "X = 1\n")
        self.commit(EVE, "feat: x")
        self.edit(c, "review.md", "blockers: 0\n")
        self.commit(DAN, "docs(001): review")
        self.sign(c, 4, DAN)
        self.assertEqual(self.sign(c, 4, EVE, expect_ok=False).returncode, 1)

    def test_single_superdev_rule_skipped(self):
        self.set_people(devs=(DAN,))
        c = self.ready_for_gate4()
        self.write("app/x.py", "X = 1\n")
        self.commit(DAN, "feat: x")
        res = self.sign(c, 4, DAN)
        self.assertNotIn("peer review", res.stdout + res.stderr)

    def test_no_merge_base_skipped_with_note(self):
        self.write("pod.yml", pod_text(extra="base_branch: trunk\n"))
        c = self.ready_for_gate4()
        git(self.root, "checkout", "-q", "--orphan", "trunk")
        git(self.root, "rm", "-rq", "--cached", ".")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "unrelated")
        git(self.root, "checkout", "-q", "-f", "change/001")
        self.write("app/x.py", "X = 1\n")
        self.commit(DAN, "feat: x")
        res = self.sign(c, 4, DAN)
        self.assertIn("note: peer review skipped: no merge base between HEAD and trunk", res.stdout)

    def test_every_superdev_wrote_code_falls_back(self):
        c = self.ready_for_gate4()
        self.write("app/x.py", "X = 1\n")
        self.commit(DAN, "feat: x")
        self.write("app/y.py", "Y = 1\n")
        self.commit(EVE, "feat: y")
        res = self.sign(c, 4, DAN)
        self.assertIn("note: peer review falls back: every SuperDev wrote code", res.stdout)

    def test_prefers_origin_base(self):
        c = self.ready_for_gate4()
        self.write("app/x.py", "X = 1\n")
        self.commit(DAN, "feat: x")
        # origin/main points at the branch tip, so nothing is left to review against it
        git(self.root, "update-ref", "refs/remotes/origin/main", "HEAD")
        res = self.sign(c, 4, DAN)
        self.assertIn("no code commits (outside docs/) between origin/main and HEAD", res.stdout)


# ---------- pr-check with seat sets ----------

class MultiPrCheckTests(MultiRepo):
    """pod.yml is in docs/risk-paths, so set_people() runs before branch_off_main() commits it to main."""

    def pr(self, author, approvals=""):
        return self.sh("pr-check.sh", "--author", author, "--approvals", approvals, "--base", "main")

    def code(self, person, name="x"):
        self.write("app/%s.py" % name, "V = 1\n")
        self.commit(person, "feat: %s" % name)

    def test_medium_needs_peer_superdev(self):
        self.branch_off_main()
        self.code(DAN)  # no change folder: medium rules
        res = self.pr("bot-gh", "dan-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("no approval yet from SuperDev (eve-gh), required for Risk: medium (peer review", res.stdout)
        self.assertIn("code by dan@pod.example", res.stdout)
        self.assertEqual(self.pr("bot-gh", "eve-gh").returncode, 0)
        self.assertEqual(self.pr("dan-gh", "eve-gh").returncode, 0)

    def test_low_without_auto_needs_peer_superdev(self):
        self.branch_off_main()
        self.write("docs/changes/001-x/intent.md", "# intent\nRisk: low\n")
        self.code(EVE)
        res = self.pr("bee-gh", "eve-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("SuperDev (dan-gh), required for Risk: low", res.stdout)
        self.assertEqual(self.pr("bee-gh", "dan-gh").returncode, 0)

    def test_falls_back_to_superbiz_when_no_peer(self):
        self.branch_off_main()
        self.code(DAN, "x")
        self.code(EVE, "y")
        res = self.pr("dan-gh", "eve-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("no approval yet from SuperBiz (bee-gh), required for Risk: medium "
                      "(SuperDev opened the PR, so SuperBiz must approve instead)", res.stdout)
        self.assertEqual(self.pr("dan-gh", "bee-gh").returncode, 0)
        # a non-SuperDev author: any SuperDev, as with one SuperDev
        self.assertEqual(self.pr("bot-gh", "dan-gh").returncode, 0)

    def test_high_needs_superbiz_escalation_and_peer(self):
        self.branch_off_main()
        self.write("app/payment.py", "def pay():\n    return 0\n")
        self.commit(DAN, "feat: pay")
        res = self.pr("bot-gh", "bee-gh,lee-gh,dan-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("effective Risk: high", res.stdout)
        self.assertIn("SuperDev (eve-gh), required for Risk: high (peer review", res.stdout)
        self.assertEqual(self.pr("bot-gh", "bee-gh,lee-gh,eve-gh").returncode, 0)
        res = self.pr("bot-gh", "eve-gh")
        self.assertIn("SuperBiz (bee-gh)", res.stdout)
        self.assertIn("escalation (lee-gh)", res.stdout)

    def test_approver_equal_to_author_is_rejected(self):
        self.set_people(bizs=(BEE, BO))
        self.branch_off_main()
        self.write("app/payment.py", "def pay():\n    return 0\n")
        self.commit(DAN, "feat: pay")
        res = self.pr("bee-gh", "bee-gh,lee-gh,eve-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("no approval yet from SuperBiz (bo-gh)", res.stdout)
        self.assertEqual(self.pr("bee-gh", "bo-gh,lee-gh,eve-gh").returncode, 0)
        res = self.pr("eve-gh", "eve-gh,bo-gh,lee-gh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("SuperDev (dan-gh)", res.stdout)

    def test_single_superdev_pod_unchanged(self):
        self.set_people(devs=(DAN,))
        self.branch_off_main()
        self.code(DAN)
        self.assertEqual(self.pr("bot-gh", "dan-gh").returncode, 0)
        res = self.pr("dan-gh", "dan-gh")
        self.assertIn("SuperBiz (bee-gh), required for Risk: medium (SuperDev opened the PR", res.stdout)


# ---------- CODEOWNERS ----------

class MultiCodeownersTests(MultiRepo):
    def test_lists_all_superdevs_and_escalation(self):
        self.set_people(escs=(LEE, ("Lu", "lu@pod.example", "lu-gh")))
        self.assertEqual(self.sh("sync-codeowners.sh").returncode, 0)
        with open(os.path.join(self.root, ".github", "CODEOWNERS"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("app/auth* @dan-gh @eve-gh @lee-gh @lu-gh\n", text)


# ---------- parallel parts with owners ----------

class ParallelOwnerTests(MultiRepo):
    def plan_change(self, owner_a, owner_b="eve@pod.example"):
        c = self.new_change()
        self.to_gate3(c, owners=((BEE, DAN), (BEE, DAN)))
        self.edit(c, "plan.md", PLAN_HEAD + CHECKPOINT +
                  "## Parallel parts\n### A\nfiles: app/a.py\ntests: tests/test_a.py\nowner: %s\n"
                  "### B\nfiles: app/b.py\ntests: tests/test_b.py\n- owner: `%s`\n" % (owner_a, owner_b))
        return c

    def test_owner_must_be_superdev(self):
        c = self.plan_change("bee@pod.example")
        res = self.sign(c, 3, DAN, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("part `### A` has owner: bee@pod.example, who is not a SuperDev in pod.yml", res.stderr)

    def test_superdev_owners_pass_and_are_printed(self):
        c = self.plan_change("Dan@pod.example")
        self.sign(c, 3, DAN)
        self.sign(c, 3, BEE)
        self.assertEqual(self.check(c).returncode, 0)
        self.write("tests/test_a.py", "from app import a\n")
        self.write("tests/test_b.py", "import app.b\n")
        res = self.sh("parallel-check.sh", c)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("(A (owner: dan@pod.example), B (owner: eve@pod.example))", res.stdout)


# ---------- installer ----------

class InstallerListSyntaxTests(TempRepo):
    def test_pod_yml_documents_list_syntax(self):
        res = run([INSTALL, self.root], self.root)
        self.assertEqual(res.returncode, 0, res.stderr)
        text = self.read("pod.yml")
        self.assertIn("comma-separated lists, aligned by position", text)
        self.assertIn("superdev_email: dan@pod.example, eve@pod.example", text)
        self.assertIn("base_branch: main", text)
        self.assertTrue(self.exists("docs/scaling.md"))
        cfg = lib.read_pod_yml(self.root)
        self.assertEqual(lib.role_emails(cfg, "superdev"), [DEV])
        self.assertEqual(lib.role_emails(cfg, "superbiz"), [BIZ])


if __name__ == "__main__":
    unittest.main()
