"""Tests for kit v3: stack keys in pod.yml, pod-install.sh, and hooks in projects without the kit."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from tests.test_pod_scripts import HOOKS_BIZ, HOOKS_DEV, POD, run
from tests.test_pod_v2 import AutoMergeRepo, git

INSTALL = os.path.join(POD, "scripts", "pod-install.sh")
REPO_ROOT = os.path.dirname(POD)


def make_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("MAKE") and k != "MFLAGS"}
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def make(root, *args):
    return subprocess.run(["make"] + list(args), cwd=root, env=make_env(),
                          capture_output=True, text=True)


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="pod-v3-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        run(["git", "init", "-q"], self.root)
        run(["git", "config", "user.name", "test"], self.root)
        run(["git", "config", "user.email", "t@example.com"], self.root)

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
            return fh.read()

    def exists(self, rel):
        return os.path.exists(os.path.join(self.root, rel))

    def install(self, *flags):
        res = run([INSTALL, self.root] + list(flags), self.root)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res

    def snapshot(self):
        files = {}
        for folder, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d != ".git"]
            for n in names:
                p = os.path.join(folder, n)
                with open(p, "rb") as fh:
                    files[os.path.relpath(p, self.root)] = (fh.read(), os.stat(p).st_mode)
        return files

    def set_pod(self, **values):
        lines = []
        for line in self.read("pod.yml").splitlines():
            key = line.split(":", 1)[0].strip()
            if key in values and not line.startswith("#"):
                line = "%s: %s" % (key, values.pop(key))
            lines.append(line)
        lines += ["%s: %s" % kv for kv in values.items()]
        self.write("pod.yml", "\n".join(lines) + "\n")

    def sh(self, name, *args):
        return run([os.path.join(self.root, "scripts", name)] + list(args), self.root)


# ---------- installer ----------

class InstallerTests(TempRepo):
    def test_empty_repo(self):
        res = self.install()
        for rel in ("scripts/lib.py", "scripts/gate.sh", "scripts/pod-test.sh", "scripts/setup-github.sh",
                    "docs/gates.md", "docs/risk-tiers.md", "docs/risk-paths", "docs/merge-by-risk.md",
                    "docs/parallel-agents.md", "docs/test-strength.md", "docs/pod-charter.md",
                    "docs/credits.md", "docs/templates/plan.md", "docs/changes/.gitkeep",
                    ".github/workflows/pod-gates.yml", "pod.yml", "pod.mk", "Makefile",
                    "AGENTS.md", "CLAUDE.md", ".gitignore", "tests/__init__.py"):
            self.assertTrue(self.exists(rel), rel)
        for rel in ("scripts/pod-install.sh", "scripts/pod_install.py", "plugins", "app",
                    "logs", ".claude-plugin", "docs/adopt.md", "tests/test_orders.py"):
            self.assertFalse(self.exists(rel), rel)
        self.assertTrue(os.access(os.path.join(self.root, "scripts", "gate.sh"), os.X_OK))
        self.assertIn("include pod.mk", self.read("Makefile"))
        self.assertIn("<!-- pod:begin -->", self.read("AGENTS.md"))
        # the block keeps the 4 kit sections the installer selects by heading, plus the stack section
        block = self.read("AGENTS.md").split("<!-- pod:begin -->", 1)[1]
        self.assertEqual(len(re.findall(r"^## ", block, re.M)), 5, block)
        self.assertEqual(self.read("CLAUDE.md"), "@AGENTS.md\n")
        self.assertEqual(self.read(".gitignore").splitlines()[-3:], [".pod/", "!**/skills/build/", "!docs/changes/*/gates.log"])
        self.assertIn("make -f pod.mk pod-check", self.read(".github/workflows/pod-gates.yml"))
        self.assertIn("Warning: ", res.stdout)
        self.assertIn("Next steps", res.stdout)
        # second run is a no-op
        before = self.snapshot()
        res = self.install()
        self.assertIn("No changes", res.stdout)
        self.assertEqual(before, self.snapshot())

    def test_existing_makefile_and_agents(self):
        makefile = "build:\n\techo build\n"
        agents = "# Team rules\n\nAlways write tests.\n"
        self.write("Makefile", makefile)
        self.write("AGENTS.md", agents)
        self.write("CLAUDE.md", "# Claude\nUse tabs.\n")
        self.write(".gitignore", "node_modules/\n.pod/\n")
        res = self.install()
        self.assertEqual(self.read("Makefile"), makefile)
        self.assertIn("include pod.mk", res.stdout)
        text = self.read("AGENTS.md")
        self.assertTrue(text.startswith(agents))
        self.assertEqual(text.count("<!-- pod:begin -->"), 1)
        self.assertTrue(text.rstrip().endswith("<!-- pod:end -->"))
        self.assertEqual(self.read("CLAUDE.md"), "# Claude\nUse tabs.\n\n@AGENTS.md\n")
        self.assertEqual(self.read(".gitignore"), "node_modules/\n.pod/\n# pod kit\n!**/skills/build/\n!docs/changes/*/gates.log\n")
        before = self.snapshot()
        res = self.install()
        self.assertIn("No changes", res.stdout)
        self.assertEqual(before, self.snapshot())
        # the block is replaced on re-run; text outside it is kept
        edited = text.replace("## Gates", "## Gates (edited)") + "\nTeam note after block.\n"
        self.write("AGENTS.md", edited)
        self.install()
        again = self.read("AGENTS.md")
        self.assertNotIn("(edited)", again)
        self.assertTrue(again.startswith(agents))
        self.assertTrue(again.endswith("\nTeam note after block.\n"))
        self.assertEqual(again.count("<!-- pod:begin -->"), 1)
        # pod-check works through pod.mk without the project Makefile
        self.assertEqual(self.sh("sync-codeowners.sh").returncode, 0)
        res = make(self.root, "-f", "pod.mk", "pod-check")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_existing_files_skipped_unless_force(self):
        self.write("docs/gates.md", "# our gates\n")
        res = self.install()
        self.assertIn("  - docs/gates.md", res.stdout)
        self.assertEqual(self.read("docs/gates.md"), "# our gates\n")
        res = self.install()
        self.assertIn("  - docs/gates.md", res.stdout)
        res = self.install("--force")
        with open(os.path.join(POD, "docs", "gates.md"), encoding="utf-8") as fh:
            self.assertEqual(self.read("docs/gates.md"), fh.read())
        self.assertEqual(self.read("docs/gates.md.pod-bak"), "# our gates\n")
        self.assertIn("docs/gates.md.pod-bak", res.stdout)

    def test_force_never_overwrites_makefile(self):
        self.write("Makefile", "x:\n\ttrue\n")
        self.install("--force")
        self.assertEqual(self.read("Makefile"), "x:\n\ttrue\n")

    def test_with_sample_passes_make_check(self):
        self.install("--with-sample")
        for rel in ("app/orders.py", "tests/test_orders.py", "logs/sample-app.log"):
            self.assertTrue(self.exists(rel), rel)
        self.assertFalse(self.exists("tests/test_pod_scripts.py"))
        self.assertIn("!logs/sample-app.log", self.read(".gitignore"))
        self.assertIn("strength: python", self.read("pod.yml"))
        self.assertEqual(self.sh("sync-codeowners.sh").returncode, 0)
        res = make(self.root, "check")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("no weak tests", res.stdout)

    def test_vendor_plugins(self):
        self.install("--vendor-plugins")
        hook = os.path.join(self.root, "plugins", "superdev", "hooks", "gate-guard.sh")
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertTrue(self.exists("plugins/superbiz/.claude-plugin/plugin.json"))

    def test_not_a_git_repo(self):
        plain = os.path.realpath(tempfile.mkdtemp(prefix="pod-v3-plain-"))
        self.addCleanup(shutil.rmtree, plain, ignore_errors=True)
        res = run([INSTALL, plain], plain)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(os.listdir(plain), [])


class StackDetectionTests(TempRepo):
    def stack(self):
        values = {}
        for line in self.read("pod.yml").splitlines():
            key, _, rest = line.partition(":")
            if key in ("test_cmd", "code_dirs", "tests_dir", "strength"):
                values[key] = rest.split("#", 1)[0].strip()
        return values

    def test_package_json(self):
        self.write("package.json", '{"scripts": {"test": "node -e 0"}}\n')
        os.makedirs(os.path.join(self.root, "__tests__"))
        self.install()
        self.assertEqual(self.stack(), {"test_cmd": "npm test", "code_dirs": "src",
                                        "tests_dir": "__tests__", "strength": "off"})
        self.assertFalse(self.exists("tests"))

    def test_pyproject_with_one_package(self):
        self.write("pyproject.toml", "[project]\nname = 'shop'\n")
        self.write("shop/__init__.py", "")
        self.install()
        self.assertEqual(self.stack(), {
            "test_cmd": "python3 -m unittest discover -s tests -t . -v", "code_dirs": "shop",
            "tests_dir": "tests", "strength": "python"})

    def test_requirements_without_package_uses_src(self):
        self.write("requirements.txt", "")
        self.install()
        self.assertEqual(self.stack()["code_dirs"], "src")

    def test_go_mod(self):
        self.write("go.mod", "module example.com/x\n")
        res = self.install()
        stack = self.stack()
        self.assertEqual(stack["test_cmd"], "go test ./...")
        self.assertEqual(stack["strength"], "off")
        self.assertIn("go (go.mod)", res.stdout)


# ---------- pod-test and test-strength modes ----------

class InstalledRepoTests(TempRepo):
    def setUp(self):
        super().setUp()
        self.install()
        self.assertEqual(self.sh("sync-codeowners.sh").returncode, 0)

    def test_pod_check_without_tests_and_strength_off(self):
        self.set_pod(strength="off")
        res = make(self.root, "-f", "pod.mk", "pod-check")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("no tests yet (exit 5)", res.stdout)
        self.assertIn("test-strength is off in pod.yml", res.stdout)
        # once a change exists, "no tests ran" is a failure
        self.write("docs/changes/001-first/intent.md", "# intent\nRisk: low\n")
        res = self.sh("pod-test.sh")
        self.assertEqual(res.returncode, 5, res.stdout)
        self.assertIn("docs/changes/ already has a change", res.stdout)

    def test_pod_test_uses_test_cmd(self):
        self.set_pod(test_cmd="echo custom-run && exit 3")
        res = self.sh("pod-test.sh")
        self.assertEqual(res.returncode, 3)
        self.assertIn("custom-run", res.stdout)
        self.set_pod(test_cmd="echo ok-run")
        res = make(self.root, "test")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("ok-run", res.stdout)

    def test_strength_off(self):
        self.set_pod(strength="off")
        res = self.sh("test-strength.sh")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(),
                         "test-strength is off in pod.yml (this stack is not supported yet). "
                         "The reviewer checks for weak test patterns from docs/test-strength.md instead")

    def test_strength_cmd(self):
        self.set_pod(strength="cmd", strength_cmd="echo WEAK x.y && exit 1")
        res = self.sh("test-strength.sh")
        self.assertEqual(res.returncode, 1)
        self.assertIn("WEAK x.y", res.stdout)
        self.set_pod(strength_cmd="exit 0")
        self.assertEqual(self.sh("test-strength.sh").returncode, 0)
        self.set_pod(strength_cmd="")
        res = self.sh("test-strength.sh")
        self.assertEqual(res.returncode, 2)
        self.assertIn("has no strength_cmd", res.stdout)

    def test_strength_python_with_src_layout_and_custom_dirs(self):
        self.set_pod(code_dirs="src", tests_dir="checks",
                     test_cmd="python3 -m unittest discover -s checks -t . -v")
        self.write("src/shop/__init__.py", "")
        self.write("src/shop/cart.py", "def total(items):\n    return sum(items)\n\n\n"
                                       "def first(items):\n    return items[0] if items else None\n")
        self.write("checks/__init__.py", "")
        self.write("checks/test_cart.py",
                   "import sys, unittest\nsys.path.insert(0, 'src')\nfrom shop import cart\n\n\n"
                   "class T(unittest.TestCase):\n"
                   "    def test_total(self):\n        self.assertEqual(cart.total([1, 2]), 3)\n\n"
                   "    def test_first_empty(self):\n        self.assertIsNone(cart.first([]))\n")
        res = self.sh("test-strength.sh")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("WEAK checks.test_cart.T.test_first_empty", res.stdout)
        self.assertNotIn("test_total", res.stdout)
        self.assertIn("src/", res.stdout)

    def test_unknown_strength_mode(self):
        self.set_pod(strength="maybe")
        self.assertEqual(self.sh("test-strength.sh").returncode, 2)


# ---------- auto-merge with stack keys ----------

class AutoMergeV3Tests(AutoMergeRepo):
    def append_pod(self, text):
        with open(os.path.join(self.root, "pod.yml"), "a", encoding="utf-8") as fh:
            fh.write(text)

    def test_deny_when_strength_off(self):
        self.assertEqual(self.auto().returncode, 0)
        self.append_pod("strength: off\n")
        self.assert_deny("test-strength is off, so auto-merge is not allowed")

    def test_deny_when_test_cmd_fails(self):
        self.append_pod("test_cmd: exit 1\n")
        self.assert_deny("make test failed")

    def test_custom_tests_dir_deletion_rule(self):
        # add checks/ on main, bring it into the branch, then delete a line on the branch
        git(self.root, "checkout", "-q", "main")
        self.write("checks/cases.txt", "case one\ncase two\n")
        self.commit("test: checks")
        git(self.root, "checkout", "-q", "change/003")
        git(self.root, "merge", "-q", "--no-edit", "main")
        self.write("checks/cases.txt", "case one\n")
        self.commit("test: drop case")
        self.append_pod("tests_dir: checks\n")
        res = self.assert_deny("deleted or changed lines in checks/: 1")
        self.assertNotIn("in tests/", res.stdout)


# ---------- hooks: protect-tests with tests_dir, and projects without the kit ----------

class HookV3Tests(TempRepo):
    def hook(self, path, payload, root=None):
        return run([path], self.root, env={"CLAUDE_PROJECT_DIR": root or self.root},
                   stdin=json.dumps(payload))

    def edit_payload(self, rel):
        return {"tool_name": "Edit", "tool_input": {"file_path": rel}, "cwd": self.root}

    def lock(self, name):
        os.makedirs(os.path.join(self.root, ".pod"), exist_ok=True)
        open(os.path.join(self.root, ".pod", name), "w").close()

    def test_protect_tests_uses_tests_dir(self):
        self.write("pod.yml", "tests_dir: spec/   # custom\n")
        self.lock("lock-tests")
        hook = os.path.join(HOOKS_DEV, "protect-tests.sh")
        res = self.hook(hook, self.edit_payload("spec/cart_test.py"))
        self.assertEqual(res.returncode, 2)
        self.assertIn("spec/cart_test.py", res.stderr)
        self.assertEqual(self.hook(hook, self.edit_payload("tests/x.py")).returncode, 0)
        self.assertEqual(self.hook(hook, self.edit_payload("specs/x.py")).returncode, 0)

    def test_hooks_allow_in_project_without_pod(self):
        self.lock("kill-switch")
        self.lock("lock-tests")
        cases = [
            (os.path.join(HOOKS_DEV, "kill-switch.sh"),
             {"tool_name": "Read", "tool_input": {"file_path": "a"}, "cwd": self.root}),
            (os.path.join(HOOKS_DEV, "protect-tests.sh"), self.edit_payload("tests/t.py")),
            (os.path.join(HOOKS_DEV, "gate-guard.sh"),
             {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}, "cwd": self.root}),
            (os.path.join(HOOKS_BIZ, "biz-scope.sh"), self.edit_payload("src/app.js")),
        ]
        for hook, payload in cases:
            res = self.hook(hook, payload)
            self.assertEqual(res.returncode, 0, (hook, res.stderr))
            self.assertIn("No pod kit in this project", res.stderr)
            self.assertEqual(len(res.stderr.strip().splitlines()), 1, res.stderr)

    def test_gate_guard_and_biz_scope_allow_without_scripts(self):
        self.write("pod.yml", "superbiz_email: b@example.com\n")
        res = self.hook(os.path.join(HOOKS_DEV, "gate-guard.sh"),
                        {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 1"}})
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("No pod kit", res.stderr)
        res = self.hook(os.path.join(HOOKS_BIZ, "biz-scope.sh"), self.edit_payload("src/a.py"))
        self.assertEqual(res.returncode, 0, res.stderr)
        # kill-switch is active as soon as pod.yml exists
        self.lock("kill-switch")
        res = self.hook(os.path.join(HOOKS_DEV, "kill-switch.sh"), {"tool_name": "Read", "cwd": self.root})
        self.assertEqual(res.returncode, 2)

    def test_hooks_still_block_in_installed_project(self):
        self.install_kit()
        res = self.hook(os.path.join(HOOKS_BIZ, "biz-scope.sh"), self.edit_payload("src/a.py"))
        self.assertEqual(res.returncode, 2)
        res = self.hook(os.path.join(HOOKS_DEV, "gate-guard.sh"),
                        {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}})
        self.assertEqual(res.returncode, 2)

    def install_kit(self):
        res = run([INSTALL, self.root], self.root)
        self.assertEqual(res.returncode, 0, res.stderr)


# ---------- config and marketplace ----------

class ConfigTests(unittest.TestCase):
    def test_kit_pod_yml_matches_defaults(self):
        import sys
        sys.path.insert(0, os.path.join(POD, "scripts"))
        import lib
        cfg = lib.read_pod_yml(POD)
        for key, value in lib.STACK_DEFAULTS.items():
            self.assertEqual(cfg[key], value, key)

    def test_marketplaces_and_versions(self):
        versions = set()
        for plugin in ("superbiz", "superdev"):
            with open(os.path.join(POD, "plugins", plugin, ".claude-plugin", "plugin.json")) as fh:
                versions.add(json.load(fh)["version"])
        self.assertEqual(versions, {"0.5.1"})
        bases = [(POD, "./plugins/")]
        for base, prefix in bases:
            with open(os.path.join(base, ".claude-plugin", "marketplace.json")) as fh:
                market = json.load(fh)
            self.assertEqual(market["name"], "tripod")
            self.assertEqual(market["metadata"]["version"], "0.5.1")
            for entry in market["plugins"]:
                self.assertEqual(entry["source"], prefix + entry["name"])
                self.assertTrue(os.path.isdir(os.path.join(base, entry["source"])), entry["source"])


if __name__ == "__main__":
    unittest.main()
