"""Tests for change 006: new-change.sh sees changes on other branches (numbering and the WIP limit)."""
import os
import shutil
import tempfile

from tests.test_pod_scripts import PodRepo, run


class BranchRepo(PodRepo):
    def setUp(self):
        super().setUp()
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.git("branch", "-M", "main")

    def git(self, *args):
        res = run(["git"] + list(args), self.root)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def on_branch(self, slug, gates=(1,), risk="low"):
        """Start a change from main on its own change/NNN-slug branch, sign `gates`, commit, return to main."""
        self.git("checkout", "-q", "main")
        self.git("checkout", "-q", "-b", "wip-" + slug)
        path = self.new_change(slug, risk)
        for gate in gates:
            self.pass_gate(path, gate, risk)
        name = os.path.basename(path)
        self.git("add", "-A")
        self.git("commit", "-qm", name)
        self.git("branch", "-m", "change/" + name)
        self.git("checkout", "-q", "main")
        return name

    def start(self, slug):
        return self.sh("new-change.sh", slug)


class NumberingTests(BranchRepo):
    def test_numbers_continue_above_other_branches(self):
        self.assertEqual(self.on_branch("a"), "001-a")
        self.assertEqual(self.on_branch("b", gates=()), "002-b")  # a draft still takes a number
        res = self.start("c")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "docs/changes/003-c")

    def test_branch_without_a_folder_still_takes_its_number(self):
        self.git("branch", "change/009-ghost")
        self.assertEqual(self.start("x").stdout.strip(), "docs/changes/010-x")

    def test_existing_duplicates_count_and_numbering_continues(self):
        self.on_branch("a")  # 001-a
        self.git("checkout", "-q", "-b", "change/001-b")  # an old collision: a second 001, made by hand
        path = os.path.join(self.root, "docs/changes/001-b")
        os.makedirs(path)
        shutil.copy(os.path.join(self.root, "docs/templates/intent.md"), os.path.join(path, "intent.md"))
        self.pass_gate(path, 1)
        self.git("add", "-A")
        self.git("commit", "-qm", "dup")
        self.git("checkout", "-q", "main")
        res = self.start("c")
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - 001-a (branch change/001-a)", res.stderr)
        self.assertIn("  - 001-b (branch change/001-b)", res.stderr)
        self.git("checkout", "-q", "change/001-a")
        for gate in (2, 3, 4):
            self.pass_gate(os.path.join(self.root, "docs/changes/001-a"), gate)
        self.git("add", "-A")
        self.git("commit", "-qm", "finish a")
        self.git("checkout", "-q", "main")
        res = self.start("c")
        self.assertEqual((res.returncode, res.stdout.strip()), (0, "docs/changes/002-c"))

    def test_branch_without_gates_log_is_not_open(self):
        a = self.on_branch("a")
        self.on_branch("b")
        self.git("checkout", "-q", "change/" + a)
        self.git("rm", "-q", "docs/changes/%s/gates.log" % a)
        self.git("commit", "-qm", "drop log")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.start("c").returncode, 0)


class WipTests(BranchRepo):
    def test_open_changes_on_branches_reach_the_limit(self):
        a, b = self.on_branch("a"), self.on_branch("b")
        res = self.start("c")
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout, "")
        self.assertIn("Refused: 2 open changes reach the WIP limit (2)", res.stderr)
        self.assertIn("  - %s (branch change/%s)" % (a, a), res.stderr)
        self.assertIn("  - %s (branch change/%s)" % (b, b), res.stderr)
        self.assertIn("delete its branch", res.stderr)
        self.assertNotIn("git fetch", res.stderr)

    def test_drafts_do_not_count(self):
        self.on_branch("a")
        self.on_branch("b", gates=())
        self.assertEqual(self.start("c").returncode, 0)

    def test_finished_change_does_not_count(self):
        self.on_branch("a", gates=(1, 2, 3, 4))
        self.on_branch("b")
        self.assertEqual(self.start("c").returncode, 0)

    def test_working_tree_wins_over_its_own_branch(self):
        a = self.on_branch("a")  # its branch has gate 1 only
        self.on_branch("b")
        path = os.path.join(self.root, "docs/changes", a)  # on main: a finished copy, not committed
        os.makedirs(path)
        with open(os.path.join(path, "intent.md"), "w", encoding="utf-8") as fh:
            fh.write(self.git("show", "change/%s:docs/changes/%s/intent.md" % (a, a)))
        for gate in (1, 2, 3, 4):
            self.pass_gate(path, gate)
        res = self.start("c")
        self.assertEqual((res.returncode, res.stdout.strip()), (0, "docs/changes/003-c"), res.stderr)

    def test_working_tree_change_is_named_as_such(self):
        self.on_branch("a")
        self.git("checkout", "-q", "-b", "change/002-b")
        self.pass_gate(self.new_change("b"), 1)
        res = self.start("c")
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - 002-b (working tree)", res.stderr)


class RemoteTests(BranchRepo):
    def setUp(self):
        super().setUp()
        self.remote = os.path.realpath(tempfile.mkdtemp(prefix="pod-remote-"))
        self.addCleanup(shutil.rmtree, self.remote, ignore_errors=True)
        run(["git", "init", "-q", "--bare", self.remote], self.root)
        self.git("remote", "add", "origin", self.remote)
        self.git("push", "-q", "origin", "main")

    def push_and_forget(self, name):
        self.git("push", "-q", "origin", "change/" + name)
        self.git("branch", "-D", "change/" + name)
        self.git("fetch", "-q", "origin")

    def test_remote_tracking_branches_count(self):
        a = self.on_branch("a")
        self.push_and_forget(a)
        self.on_branch("b")
        res = self.start("c")
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - %s (branch origin/change/%s)" % (a, a), res.stderr)
        self.assertIn("git fetch", res.stderr)

    def test_remote_numbers_are_skipped(self):
        self.push_and_forget(self.on_branch("a", gates=()))
        self.assertEqual(self.start("b").stdout.strip(), "docs/changes/002-b")

    def test_local_branch_wins_over_remote(self):
        a = self.on_branch("a")
        self.git("push", "-q", "origin", "change/" + a)
        self.git("checkout", "-q", "change/" + a)
        for gate in (2, 3, 4):
            self.pass_gate(os.path.join(self.root, "docs/changes", a), gate)
        self.git("add", "-A")
        self.git("commit", "-qm", "finish")
        self.git("checkout", "-q", "main")
        self.on_branch("b")
        self.assertEqual(self.start("c").returncode, 0)  # local a is finished; origin's copy is older


    def test_pushed_current_branch_keeps_its_number(self):
        self.on_branch("a", gates=())
        self.git("checkout", "-q", "-b", "change/002-x")
        self.git("push", "-q", "origin", "change/002-x")
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.start("x").stdout.strip(), "docs/changes/002-x")


class FallbackTests(BranchRepo):
    def test_without_git_it_works_as_before(self):
        shutil.rmtree(os.path.join(self.root, ".git"))
        res = self.start("a")
        self.assertEqual((res.returncode, res.stdout.strip()), (0, "docs/changes/001-a"))
        self.assertEqual(self.start("b").stdout.strip(), "docs/changes/002-b")

    def test_usage_is_unchanged(self):
        self.assertEqual(self.start("Bad Slug").returncode, 2)
