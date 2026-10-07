#!/usr/bin/env python3
"""Test strength: does each test observe behavior of app/?

For every test in tests/ whose module imports `app`, run it twice:
1. normally (it should pass; a normal failure is reported but left to `make test`)
2. with every plain function defined in app/*.py replaced by a stub returning None

A test that still passes in run 2 cannot fail for a defect in app/, so it is weak.
Exit 1 when any weak test is found.

usage: python3 scripts/strength.py
"""
import ast
import glob
import importlib
import inspect
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HINT = ("test นี้ยังผ่านแม้ทุกฟังก์ชันใน app/ คืนค่า None ให้ assert ผลลัพธ์จริงด้วยค่าที่ระบุชัด "
        "หรือจับคู่กรณีไม่มีข้อมูลกับกรณีมีข้อมูลใน test เดียวกัน")


def imports_app(path):
    """True when the module source imports `app` or `app.<x>` (by AST, not text)."""
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == "app" or node.module.startswith("app."):
                return True
        if isinstance(node, ast.Import):
            if any(a.name == "app" or a.name.startswith("app.") for a in node.names):
                return True
    return False


def app_modules():
    mods = []
    for path in sorted(glob.glob(os.path.join(ROOT, "app", "*.py"))):
        name = os.path.splitext(os.path.basename(path))[0]
        mods.append(importlib.import_module("app" if name == "__init__" else "app." + name))
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
    """Replace app functions (and test-module aliases of them) with `stub`, then restore."""

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


def main():
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)
    tests_dir = os.path.join(ROOT, "tests")
    if not os.path.isdir(tests_dir):
        print("test-strength: ไม่พบโฟลเดอร์ tests/")
        return 0
    loader = unittest.TestLoader()
    suite = loader.discover("tests", top_level_dir=ROOT)
    selected, test_modules = [], {}
    for test in iter_tests(suite):
        if isinstance(test, unittest.loader._FailedTest):  # import error: make test reports it
            print("ข้าม %s: import ไม่ได้ (ให้ make test แสดงรายละเอียด)" % test.id())
            continue
        mod = sys.modules.get(type(test).__module__)
        path = getattr(mod, "__file__", "") or ""
        if mod is not None and imports_app(path):
            selected.append(test.id())
            test_modules[mod.__name__] = mod
    modules = app_modules() if selected else []
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
        print("FAIL (ปกติ) %s: ไม่ผ่านตั้งแต่รันปกติ ให้ดูผลจาก make test" % test_id)
    for test_id in weak:
        print("WEAK %s\n  %s" % (test_id, HINT))
    if weak:
        print("test-strength: พบ test ที่อ่อน %d จาก %d test" % (len(weak), checked))
        return 1
    print("test-strength: ตรวจแล้ว %d test ไม่มี test ที่อ่อน" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
