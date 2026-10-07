#!/usr/bin/env python3
"""Test strength: does each test observe behavior of the code?

The mode comes from `strength` in pod.yml (see docs/test-strength.md):
- python: for every test in `tests_dir` whose module imports a package from `code_dirs`, run it twice:
  1. normally (it should pass; a normal failure is reported but left to the test command)
  2. with every plain function defined in modules under `code_dirs` replaced by a stub returning None
  A test that still passes in run 2 cannot fail for a defect in the code, so it is weak.
  Exit 1 when any weak test is found.
- off: print a notice and exit 0 (auto-merge-check then denies, it needs a measured strength).
- cmd: run `strength_cmd` and exit with its code (a team check for another stack).

usage: python3 scripts/strength.py
"""
import ast
import importlib
import inspect
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

ROOT = lib.ROOT
OFF_MESSAGE = ("test-strength is off in pod.yml (this stack is not supported yet). "
               "The reviewer checks for weak test patterns from docs/test-strength.md instead")
SKIP_DIRS = {"__pycache__", "node_modules", "venv", ".venv", ".git", ".pod"}


def hint(dirs):
    return ("this test still passes when every function in %s returns None. Assert the real result "
            "against an explicit value, or pair the empty case with a non-empty case in the same test" % ", ".join(d + "/" for d in dirs))


def code_modules(dirs, tests_dir):
    """Map of import name -> source path for every .py file under the code dirs.

    A dir with __init__.py is a package imported from the project root (app -> app.orders).
    A dir without it is a source root added to sys.path (src/shop/cart.py -> shop.cart).
    """
    found = {}
    tests_abs = os.path.join(ROOT, tests_dir)
    for d in dirs:
        base = os.path.normpath(os.path.join(ROOT, d))
        if not os.path.isdir(base):
            continue
        is_pkg = os.path.isfile(os.path.join(base, "__init__.py")) and base != ROOT
        source_root = os.path.dirname(base) if is_pkg else base
        if source_root not in sys.path:
            sys.path.insert(0, source_root)
        for folder, subdirs, files in os.walk(base):
            subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS and not s.startswith("."))
            if os.path.normpath(folder) == ROOT:  # code_dirs "." : skip the pod kit itself
                subdirs[:] = [s for s in subdirs if s not in ("scripts", "plugins", "docs")]
            if os.path.normpath(folder) == os.path.normpath(tests_abs) or \
                    os.path.normpath(folder).startswith(os.path.normpath(tests_abs) + os.sep):
                subdirs[:] = []
                continue
            for name in sorted(files):
                if not name.endswith(".py") or name.startswith("test_") or name == "setup.py":
                    continue
                rel = os.path.relpath(os.path.join(folder, name), source_root)
                parts = rel[:-3].split(os.sep)
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                if not parts or not all(p.isidentifier() for p in parts):
                    continue
                found.setdefault(".".join(parts), os.path.join(folder, name))
    return found


def imports_code(path, tops):
    """True when the module source imports one of the code packages (by AST, not text)."""
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.split(".")[0] in tops:
                return True
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[0] in tops for a in node.names):
                return True
    return False


def load_modules(names):
    mods = []
    for name in sorted(names):
        try:
            mods.append(importlib.import_module(name))
        except Exception as exc:  # noqa: BLE001 - a module that cannot import is reported, not fatal
            print("skip module %s: import failed (%s)" % (name, type(exc).__name__))
    return mods


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def stub(*_args, **_kwargs):
    return None


class Stubbed:
    """Replace code functions (and test-module aliases of them) with `stub`, then restore."""

    def __init__(self, modules, test_modules):
        self.targets = []
        originals = set()
        for mod in modules:
            for name, obj in list(vars(mod).items()):
                if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
                    self.targets.append((mod, name, obj))
                    originals.add(id(obj))
        # `from app.x import f` in a test module keeps its own reference: stub that too
        for mod in test_modules:
            for name, obj in list(vars(mod).items()):
                if inspect.isfunction(obj) and id(obj) in originals:
                    self.targets.append((mod, name, obj))

    def __enter__(self):
        for mod, name, _ in self.targets:
            setattr(mod, name, stub)
        return self

    def __exit__(self, *exc):
        for mod, name, obj in self.targets:
            setattr(mod, name, obj)
        return False


def run_one(loader, test_id):
    result = unittest.TestResult()
    loader.loadTestsFromName(test_id).run(result)
    passed = result.wasSuccessful() and not result.skipped
    return passed, bool(result.skipped)


def run_cmd_mode(cfg):
    if not cfg["strength_cmd"]:
        print("test-strength: pod.yml sets strength: cmd but has no strength_cmd")
        return 2
    print("test-strength: %s" % cfg["strength_cmd"], flush=True)
    return subprocess.run(cfg["strength_cmd"], shell=True, cwd=ROOT).returncode


def main():
    cfg = lib.read_pod_yml(ROOT, missing_ok=True)
    mode = cfg["strength"]
    if mode == "off":
        print(OFF_MESSAGE)
        return 0
    if mode == "cmd":
        return run_cmd_mode(cfg)
    if mode != "python":
        print("test-strength: pod.yml has unknown strength: %s (allowed: %s)"
              % (mode, " | ".join(lib.STRENGTH_MODES)))
        return 2
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)
    tests_dir = cfg["tests_dir"]
    dirs = lib.code_dirs(cfg)
    if not os.path.isdir(os.path.join(ROOT, tests_dir)):
        print("test-strength: folder %s/ not found" % tests_dir)
        return 0
    names = code_modules(dirs, tests_dir)
    tops = {n.split(".")[0] for n in names}
    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir, top_level_dir=ROOT)
    selected, test_modules = [], {}
    for test in iter_tests(suite):
        if isinstance(test, unittest.loader._FailedTest):  # import error: the test command reports it
            print("skip %s: import failed (make test shows the details)" % test.id())
            continue
        mod = sys.modules.get(type(test).__module__)
        path = getattr(mod, "__file__", "") or ""
        if mod is not None and imports_code(path, tops):
            selected.append(test.id())
            test_modules[mod.__name__] = mod
    modules = load_modules(names) if selected else []
    weak, broken, checked = [], [], 0
    for test_id in selected:
        passed, skipped = run_one(loader, test_id)
        if skipped:
            continue
        if not passed:
            broken.append(test_id)
            continue
        checked += 1
        with Stubbed(modules, test_modules.values()):
            still_passes, _ = run_one(loader, test_id)
        if still_passes:
            weak.append(test_id)
    for test_id in broken:
        print("FAIL (normal run) %s: fails even in a normal run. See the output of make test" % test_id)
    for test_id in weak:
        print("WEAK %s\n  %s" % (test_id, hint(dirs)))
    if weak:
        print("test-strength: found %d weak tests out of %d" % (len(weak), checked))
        return 1
    print("test-strength: checked %d tests, no weak tests" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
