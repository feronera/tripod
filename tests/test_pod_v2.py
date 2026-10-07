"""Tests for kit v2: plan structure, test strength, risk-based merge and PR identity."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from tests.test_pod_scripts import BIZ, DEV, LEAD, HOOKS_DEV, POD, VALID_PLAN, PodRepo, run

sys.path.insert(0, os.path.join(POD, "scripts"))
import lib  # noqa: E402

PLAN_HEAD = "# plan\n## Data shape\ndict order_id -> record\n"
CHECKPOINT = ("## Throughput checkpoint\n- Blocking first steps: failing tests\n"
              "- Independent workstreams: n/a: one file\n- Shared mutable state: none\n"
              "- Smallest safe decomposition: one requirement per commit\n")

CALC = '''def add(a, b):
    return a + b


def find(key):
    return {"a": 1}.get(key)
'''
CALC_TESTS = '''import unittest

from app import calc


class CalcTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calc.add(1, 2), 3)

    def test_find(self):
        self.assertIsNone(calc.find("zz"))
        self.assertEqual(calc.find("a"), 1)
'''


def git(root, *args):
    res = run(["git"] + list(args), root)
    assert res.returncode == 0, (args, res.stdout, res.stderr)
    return res.stdout.strip()


class V2Repo(PodRepo):
    """PodRepo plus docs/risk-paths and the v2 pod.yml keys."""

    def setUp(self):
        super().setUp()
        shutil.copy(os.path.join(POD, "docs", "risk-paths"),
                    os.path.join(self.root, "docs", "risk-paths"))

    def write_pod_yml(self, biz=BIZ, dev=DEV, wip=2, auto="off", max_lines=200, track=2,
                      hours=48):
        with open(os.path.join(self.root, "pod.yml"), "w", encoding="utf-8") as fh:
            fh.write("superbiz_name: Biz\nsuperbiz_email: %s\nsuperdev_name: Dev\n"
                     "superdev_email: %s\nescalation_name: Lead\nescalation_email: %s\n"
                     "wip_limit: %d\nsuperbiz_github: biz-example\nsuperdev_github: dev-example\n"
                     "escalation_github: lead-example\nauto_merge: %s   # off | low\n"
                     "auto_merge_max_lines: %d\nauto_merge_min_track: %d\nacceptance_hours: %d\n"
                     % (biz, dev, LEAD, wip, auto, max_lines, track, hours))

    def to_gate(self, change, upto, risk="low"):
        for gate in range(1, upto + 1):
            self.pass_gate(change, gate, risk)

    def write(self, rel_path, text, mode="w"):
        path = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode, encoding="utf-8") as fh:
            fh.write(text)

    def log_lines(self, change):
        with open(os.path.join(change, "gates.log"), encoding="utf-8") as fh:
            return fh.read().splitlines()


# ---------- A. plan.md structure at gate 3 ----------

class PlanCheckTests(V2Repo):
    def plan_change(self, plan):
        c = self.new_change()
        self.to_gate(c, 2)
        self.edit(c, "plan.md", plan)
        return c

    def assert_refused(self, c, *needles):
        res = self.approve(c, 3, DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertFalse(any("gate=3" in l for l in self.log_lines(c)))
        for n in needles:
            self.assertIn(n, res.stderr)
        # a hand-signed log is still failed by gate-check
        b = self.blob(c, "plan.md")
        with open(os.path.join(c, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("gate=3 role=owner by=%s at=2026-01-01T09:00:00+07:00 blob=%s\n" % (DEV, b))
            fh.write("gate=3 role=cross by=%s at=2026-01-01T09:05:00+07:00 blob=%s\n" % (BIZ, b))
        res = self.check(c)
        self.assertEqual(res.returncode, 1, res.stdout)
        for n in needles:
            self.assertIn(n, res.stdout)

    def test_missing_checkpoint_is_refused(self):
        c = self.plan_change(PLAN_HEAD + "## Parallel parts\nnone: small\n")
        self.assert_refused(c, "## Throughput checkpoint")

    def test_placeholder_checkpoint_value_is_refused(self):
        plan = VALID_PLAN.replace("- Shared mutable state: app/orders.py",
                                  "- Shared mutable state: <files edited in common>")
        c = self.plan_change(plan)
        self.assert_refused(c, "`Shared mutable state` has no value")

    def test_missing_checkpoint_line_and_data_shape(self):
        plan = ("# plan\n## Data shape\n<data shape>\n" + CHECKPOINT.replace(
            "- Blocking first steps: failing tests\n", "") + "## Parallel parts\nnone: x\n")
        c = self.plan_change(plan)
        self.assert_refused(c, "`## Data shape`", "`- Blocking first steps:`")

    def test_na_needs_reason(self):
        plan = VALID_PLAN.replace("n/a: one small file", "n/a")
        c = self.plan_change(plan)
        self.assert_refused(c, "Independent workstreams")

    def test_overlapping_parallel_files_fail(self):
        plan = (PLAN_HEAD + CHECKPOINT + "## Parallel parts\n### A\nfiles: app/a.py, app/b.py\n"
                "### B\nfiles: app/c.py, app/b.py\n")
        c = self.plan_change(plan)
        self.assert_refused(c, "app/b.py (A, B)")

    def test_single_part_fails(self):
        plan = PLAN_HEAD + CHECKPOINT + "## Parallel parts\n### A\nfiles: app/a.py\n"
        c = self.plan_change(plan)
        self.assert_refused(c, "has only 1 part")

    def test_none_is_accepted(self):
        c = self.plan_change(PLAN_HEAD + CHECKPOINT + "## Parallel parts\nnone: one file only\n")
        self.pass_gate(c, 3)
        self.assertEqual(self.check(c).returncode, 0)

    def test_disjoint_parts_are_accepted(self):
        plan = (PLAN_HEAD + CHECKPOINT + "## Parallel parts\n### A\nfiles: app/a.py, app/b.py\n"
                "### B\nfiles: app/c.py\n")
        c = self.plan_change(plan)
        self.pass_gate(c, 3)
        res = self.check(c)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_template_plan_is_refused(self):
        c = self.new_change()
        self.to_gate(c, 2)
        shutil.copy(os.path.join(self.root, "docs", "templates", "plan.md"),
                    os.path.join(c, "plan.md"))
        res = self.approve(c, 3, DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Data shape", res.stderr)


# ---------- B. test strength ----------

class StrengthTests(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="pod-strength-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        shutil.copytree(os.path.join(POD, "scripts"), os.path.join(self.root, "scripts"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        for d in ("app", "tests"):
            os.makedirs(os.path.join(self.root, d))
            open(os.path.join(self.root, d, "__init__.py"), "w").close()
        with open(os.path.join(self.root, "app", "calc.py"), "w", encoding="utf-8") as fh:
            fh.write(CALC)

    def write_test_file(self, body, name="test_calc.py"):
        with open(os.path.join(self.root, "tests", name), "w", encoding="utf-8") as fh:
            fh.write(body)

    def strength(self):
        return run([os.path.join(self.root, "scripts", "test-strength.sh")], self.root)

    def test_flags_weak_test(self):
        self.write_test_file("import unittest\nfrom app import calc\n\n\nclass T(unittest.TestCase):\n"
                        "    def test_missing(self):\n        self.assertIsNone(calc.find('zz'))\n\n"
                        "    def test_add(self):\n        self.assertEqual(calc.add(1, 2), 3)\n")
        res = self.strength()
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("WEAK tests.test_calc.T.test_missing", res.stdout)
        self.assertNotIn("test_add", res.stdout)
        self.assertIn("returns None", res.stdout)

    def test_passes_strong_tests(self):
        self.write_test_file(CALC_TESTS)
        res = self.strength()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("checked 2 tests", res.stdout)

    def test_stubs_from_import_alias(self):
        self.write_test_file("import unittest\nfrom app.calc import add\n\n\nclass T(unittest.TestCase):\n"
                        "    def test_add(self):\n        self.assertEqual(add(2, 2), 4)\n")
        res = self.strength()
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_skips_modules_without_app_import(self):
        self.write_test_file(CALC_TESTS)
        self.write_test_file("import unittest\n\n\nclass T(unittest.TestCase):\n"
                        "    def test_x(self):\n        self.assertTrue(True)\n", "test_other.py")
        res = self.strength()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("checked 2 tests", res.stdout)

    def test_sample_suite_is_strong(self):
        res = run([os.path.join(POD, "scripts", "test-strength.sh")], POD)
        self.assertEqual(res.returncode, 0, res.stdout)


# ---------- D. risk-based gate 4: merge-ready and release-ready ----------

class MergeReadyTests(V2Repo):
    def release(self, c):
        return self.sh("release-check.sh", c)

    def test_medium_merge_ready_with_owner_only(self):
        c = self.new_change(risk="medium")
        self.to_gate(c, 3)
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.approve(c, 4, DEV)
        res = self.check(c, "4")
        self.assertEqual(res.returncode, 0, res.stdout)
        res = self.release(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("missing cross", res.stdout)
        self.approve(c, 4, BIZ)
        res = self.release(c)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("RELEASE-READY", res.stdout)

    def test_low_needs_cross_or_auto(self):
        c = self.new_change()
        self.to_gate(c, 3)
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.approve(c, 4, DEV)
        res = self.check(c, "4")
        self.assertEqual(res.returncode, 1)
        self.assertIn("auto-merge", res.stdout)

    def test_high_needs_escalation(self):
        c = self.new_change(risk="high")
        self.to_gate(c, 3, risk="high")
        self.edit(c, "acceptance.md", "# acceptance\n")
        self.approve(c, 4, DEV)
        self.approve(c, 4, BIZ)
        res = self.check(c, "4")
        self.assertEqual(res.returncode, 1)
        self.assertIn("missing escalation", res.stdout)
        self.assertEqual(self.release(c).returncode, 1)
        self.approve(c, 4, LEAD)
        self.assertEqual(self.check(c, "4").returncode, 0)
        self.assertEqual(self.release(c).returncode, 0)

    def test_mark_revert_blocks_release(self):
        c = self.new_change()
        self.to_gate(c, 4)
        self.assertEqual(self.release(c).returncode, 0)
        self.as_user("someone@else.com")
        self.assertEqual(self.sh("mark-revert.sh", c, "x").returncode, 1)
        self.as_user(BIZ)
        res = self.sh("mark-revert.sh", c, 'error rate up "5x"')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertRegex(self.log_lines(c)[-1],
                         r'^event=revert by=biz@example.com at=\S+ reason="error rate up \'5x\'"$')
        res = self.release(c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("revert", res.stdout)
        # merge-ready (gate-check) is not changed by a revert line
        self.assertEqual(self.check(c, "4").returncode, 0)


class AutoMergeRepo(V2Repo):
    """main with 2 completed changes, then branch change/003 ready for auto-merge."""

    def setUp(self):
        super().setUp()
        self.write_pod_yml(auto="low", track=2)
        self.write("app/__init__.py", "")
        self.write("app/calc.py", CALC)
        self.write("tests/__init__.py", "")
        self.write("tests/test_calc.py", CALC_TESTS)
        self.history = [self.done_change("old-%d" % i) for i in (1, 2)]
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")
        git(self.root, "branch", "-M", "main")
        git(self.root, "checkout", "-q", "-b", "change/003")
        self.c = self.new_change("feature")
        self.to_gate(self.c, 3)
        self.write("app/calc.py", "\n\ndef double(x):\n    return x * 2\n", "a")
        self.write("tests/test_calc.py", CALC_TESTS.replace(
            "class CalcTest(unittest.TestCase):\n",
            "class CalcTest(unittest.TestCase):\n    def test_double(self):\n"
            "        self.assertEqual(calc.double(4), 8)\n\n"))
        self.commit("feat(003): double")
        self.write_review()
        self.commit("docs(003): review")

    def done_change(self, slug):
        """A completed low change, signed by writing gates.log directly (fast)."""
        c = self.new_change(slug)
        self.edit(c, "spec.md", "# spec\n")
        self.edit(c, "plan.md", VALID_PLAN)
        self.edit(c, "acceptance.md", "# acceptance\n")
        lines = []
        for gate, name in lib.ARTIFACTS.items():
            owner, cross = (BIZ, DEV) if gate in (1, 2) else (DEV, BIZ)
            b = lib.blob_hash(os.path.join(c, name))
            lines.append("gate=%d role=owner by=%s at=2026-01-0%dT09:00:00+07:00 blob=%s"
                         % (gate, owner, gate, b))
            lines.append("gate=%d role=cross by=%s at=2026-01-0%dT10:00:00+07:00 blob=%s"
                         % (gate, cross, gate, b))
        self.write_log(c, lines)
        return c

    def commit(self, msg):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", msg)

    def head(self):
        return git(self.root, "rev-parse", "HEAD")

    def write_review(self, blockers=0, opinion="agree", head=None):
        self.edit(self.c, "review.md",
                  "blockers: %d\nmajors_open: 0\nsecond_opinion: %s\nreviewed_head: %s\n\n"
                  "# Review\n" % (blockers, opinion, head or self.head()))

    def auto(self, *extra):
        return self.sh("auto-merge-check.sh", self.c, "--base", "main", *extra)

    def assert_deny(self, needle):
        res = self.auto()
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertEqual(res.stdout.splitlines()[0], "DENY")
        self.assertIn(needle, res.stdout)
        return res


class AutoMergeTests(AutoMergeRepo):
    def test_allow_and_record(self):
        res = self.auto()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(res.stdout.strip(), "ALLOW")
        self.assertFalse(any("role=auto" in l for l in self.log_lines(self.c)))
        res = self.auto("--record")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertRegex(self.log_lines(self.c)[-1],
                         r"^gate=4 role=auto by=auto-merge at=\S+ blob=- head=[0-9a-f]{40}$")
        self.assertIn("head=" + self.head(), self.log_lines(self.c)[-1])
        res = self.check(self.c, "4")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_deny_auto_merge_off(self):
        self.write_pod_yml(auto="off", track=2)
        self.assert_deny("auto_merge: off")

    def test_deny_risk_medium(self):
        self.edit(self.c, "intent.md", None, risk="medium")
        self.assert_deny("Risk in intent.md is medium")

    def test_deny_risk_path(self):
        self.write("app/auth.py", "def login():\n    return None\n")
        self.commit("feat: auth")
        self.write_review()
        self.assert_deny("touches a sensitive path: app/auth.py. The effective risk tier is high")

    def test_deny_review_blockers(self):
        self.write_review(blockers=2, head=self.head())
        self.assert_deny("blockers: 2")

    def test_deny_missing_review(self):
        os.remove(os.path.join(self.c, "review.md"))
        self.assert_deny("review.md not found")

    def test_deny_second_opinion_disagree(self):
        self.write_review(opinion="disagree")
        self.assert_deny("second_opinion: disagree")

    def test_deny_stale_reviewed_head(self):
        self.write("app/calc.py", "\n\ndef triple(x):\n    return x * 3\n", "a")
        self.commit("feat: more")
        self.assert_deny("The code changed after review")

    def test_deny_test_deletion(self):
        self.write("tests/test_calc.py", CALC_TESTS.replace(
            '        self.assertEqual(calc.find("a"), 1)\n', ""))
        self.commit("test: drop")
        self.write_review()
        self.assert_deny("deleted or changed lines in tests/: 1")

    def test_deny_weak_test(self):
        self.write("tests/test_weak.py", "import unittest\nfrom app import calc\n\n\n"
                   "class W(unittest.TestCase):\n    def test_w(self):\n"
                   "        self.assertIsNone(calc.find('q'))\n")
        self.commit("test: weak")
        self.write_review()
        self.assert_deny("test-strength failed: tests.test_weak.W.test_w")

    def test_deny_too_many_lines(self):
        self.write_pod_yml(auto="low", track=2, max_lines=1)
        self.assert_deny("over auto_merge_max_lines (1)")

    def test_deny_track_record_short(self):
        self.write_pod_yml(auto="low", track=3)
        self.assert_deny("track record has fewer than 3 changes")

    def test_deny_recent_revert(self):
        self.as_user(DEV)
        res = self.sh("mark-revert.sh", self.history[0], "rollback after incident")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assert_deny("a revert in the last")

    def test_review_commit_after_reviewed_head_is_allowed(self):
        # setUp reviewed the code commit, then committed review.md on top of it
        with open(os.path.join(self.c, "review.md"), encoding="utf-8") as fh:
            reviewed = re.search(r"reviewed_head: (\S+)", fh.read()).group(1)
        self.assertNotEqual(reviewed, self.head())
        self.assertEqual(reviewed, git(self.root, "rev-parse", "HEAD~1"))
        self.assertEqual(self.auto().returncode, 0)


class ReleaseAfterAutoTests(AutoMergeRepo):
    def test_release_waits_for_acceptance_and_overdue(self):
        self.assertEqual(self.auto("--record").returncode, 0)
        res = self.sh("release-check.sh", self.c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("waiting for SuperBiz acceptance", res.stdout)
        # pretend the auto-merge happened 3 days ago
        old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(timespec="seconds")
        lines = self.log_lines(self.c)
        lines[-1] = re.sub(r"at=\S+", "at=" + old, lines[-1])
        self.write_log(self.c, lines)
        res = self.sh("release-check.sh", self.c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Do not release to production until SuperBiz accepts", res.stdout)
        # post-merge acceptance: SuperBiz signs cross after the auto record, then SuperDev owner
        self.edit(self.c, "acceptance.md", "# acceptance\nDecision: accept\n")
        self.approve(self.c, 4, BIZ)
        res = self.sh("release-check.sh", self.c)
        self.assertEqual(res.returncode, 1)
        self.assertIn("missing owner", res.stdout)
        self.approve(self.c, 4, DEV)
        res = self.sh("release-check.sh", self.c)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_cross_without_owner_or_auto_is_refused(self):
        self.edit(self.c, "acceptance.md", "# acceptance\n")
        res = self.approve(self.c, 4, BIZ, expect_ok=False)
        self.assertEqual(res.returncode, 1)

    def test_gate_guard_allows_merge_after_auto_record(self):
        hook = os.path.join(HOOKS_DEV, "gate-guard.sh")
        payload = '{"tool_name": "Bash", "tool_input": {"command": "gh pr merge 3 --auto --squash"}}'
        env = {"CLAUDE_PROJECT_DIR": self.root}
        res = run([hook], self.root, env=env, stdin=payload)
        self.assertEqual(res.returncode, 2)
        self.assertEqual(self.auto("--record").returncode, 0)
        res = run([hook], self.root, env=env, stdin=payload)
        self.assertEqual(res.returncode, 0, res.stderr)


# ---------- E. PR approvals by risk ----------

class PrCheckTests(AutoMergeRepo):
    def pr(self, author, approvals=""):
        return self.sh("pr-check.sh", "--author", author, "--approvals", approvals,
                       "--base", "main")

    def test_low_without_auto_needs_superdev(self):
        res = self.pr("biz-example", "dev-example")
        self.assertEqual(res.returncode, 0, res.stdout)
        res = self.pr("biz-example", "")
        self.assertEqual(res.returncode, 1)
        self.assertIn("no approval yet from SuperDev (dev-example)", res.stdout)

    def test_superdev_author_needs_superbiz_instead(self):
        res = self.pr("dev-example", "dev-example")
        self.assertEqual(res.returncode, 1)
        self.assertIn("no approval yet from SuperBiz (biz-example)", res.stdout)
        self.assertEqual(self.pr("dev-example", "biz-example").returncode, 0)

    def test_medium_needs_superdev(self):
        self.edit(self.c, "intent.md", None, risk="medium")
        self.pass_gate(self.c, 1)
        self.commit("docs: medium")
        self.assertEqual(self.pr("bot-example", "dev-example").returncode, 0)
        res = self.pr("bot-example", "biz-example")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Risk: medium", res.stdout)

    def test_high_by_risk_path_needs_three(self):
        self.write("app/payment.py", "def pay():\n    return 0\n")
        self.commit("feat: pay")
        res = self.pr("bot-example", "dev-example")
        self.assertEqual(res.returncode, 1)
        self.assertIn("effective Risk: high", res.stdout)
        self.assertIn("SuperBiz (biz-example)", res.stdout)
        self.assertIn("escalation (lead-example)", res.stdout)
        self.assertEqual(self.pr("bot-example", "dev-example,biz-example,lead-example").returncode, 0)
        res = self.pr("dev-example", "lead-example")
        self.assertEqual(res.returncode, 1)
        self.assertIn("SuperBiz (biz-example)", res.stdout)
        self.assertNotIn("SuperDev (dev-example)", res.stdout)
        self.assertEqual(self.pr("dev-example", "biz-example,lead-example").returncode, 0)

    def test_low_with_auto_record_needs_no_human(self):
        self.assertEqual(self.auto("--record").returncode, 0)
        res = self.pr("dev-example", "")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_gate_log_identity_still_checked(self):
        with open(os.path.join(self.c, "gates.log"), "a", encoding="utf-8") as fh:
            fh.write("gate=3 role=cross by=x@example.com at=2026-01-01T00:00:00+07:00 blob=0\n")
        res = self.pr("biz-example", "dev-example")
        self.assertEqual(res.returncode, 1)
        self.assertIn("role mismatch", res.stdout)


class CodeownersTests(V2Repo):
    def test_sync_and_check(self):
        res = self.sh("sync-codeowners.sh", "--check")
        self.assertEqual(res.returncode, 1)
        self.assertEqual(self.sh("sync-codeowners.sh").returncode, 0)
        with open(os.path.join(self.root, ".github", "CODEOWNERS"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("app/auth* @dev-example @lead-example\n", text)
        self.assertIn("plugins/**/hooks/** @dev-example @lead-example\n", text)
        self.assertEqual(self.sh("sync-codeowners.sh", "--check").returncode, 0)

    def test_committed_codeowners_in_sync(self):
        res = run([os.path.join(POD, "scripts", "sync-codeowners.sh"), "--check"], POD)
        self.assertEqual(res.returncode, 0, res.stdout)


class ShellSyntaxTests(unittest.TestCase):
    def test_bash_n(self):
        paths = [os.path.join(POD, "scripts", n) for n in os.listdir(os.path.join(POD, "scripts"))
                 if n.endswith(".sh")]
        for plugin in ("superbiz", "superdev"):
            hooks = os.path.join(POD, "plugins", plugin, "hooks")
            paths += [os.path.join(hooks, n) for n in os.listdir(hooks) if n.endswith(".sh")]
        for p in paths:
            self.assertTrue(os.access(p, os.X_OK), p)
            res = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, (p, res.stderr))


if __name__ == "__main__":
    unittest.main()
