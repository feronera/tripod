# Test strength

A passing test does not mean the code is correct. Some tests pass even when the code does nothing at all. This document describes 5 kinds of weak test,
how `scripts/test-strength.sh` detects them in Python, and how to add a check for other stacks.

## 5 kinds of weak test

All 5 kinds still pass even when every function in the code returns an empty value (None, null or nil).

| Kind | Example | Fix |
|---|---|---|
| 1. Weak or missing assert | Only `assertTrue(x)`, `assertIsNotNone(x)`, or calling a function without checking the result | Assert the result against a specific value |
| 2. Checks only a mock or the absence of data | Only `assertIsNone(find("x"))` or `assertEqual(list_orders(), [])` | Pair it with a case that has data, in the same test |
| 3. Self-referencing | `assertEqual(f(a), f(a))`: the expected value comes from the code under test | Write the expected value from the spec |
| 4. Pinned constant | Asserts a constant or config value that is repeated from the code | Test the mechanism that uses the value |
| 5. Fixture checks fixture | Asserts data the test created itself, without calling the code under test | Call the real code and assert its result |

## Settings in pod.yml

```
test_cmd: python3 -m unittest discover -s tests -t . -v
code_dirs: app
tests_dir: tests
strength: python           # python | off | cmd
strength_cmd:
```

| `strength` | What `scripts/test-strength.sh` does | auto-merge-check |
|---|---|---|
| `python` | Runs the Python check described below. Exits 1 when a weak test is found | Uses the check result |
| `off` | Prints a message that the check is off and exits 0. The reviewer must check the 5 kinds above manually | Always DENY, because an automated merge requires a strength result |
| `cmd` | Runs `strength_cmd` and exits with that command's exit code | Uses the command's result |

## The Python check (`strength: python`)

1. Find the tests in `tests_dir` that import a package from `code_dirs`.
   - A folder in `code_dirs` that has `__init__.py` is a package (`app` gives the name `app.orders`).
   - A folder without `__init__.py` is a source root (`src/shop/cart.py` gives the name `shop.cart`).
2. Run each test normally. Tests that already fail are reported as `FAIL` and not counted.
3. Replace every function in the modules under `code_dirs` with a function that returns None, then run the test again.
4. A test that still passes in step 3 is reported as `WEAK <test id>`, because it does not fail even when the code is broken.

Limitation: only `unittest.TestCase` tests and module-level functions are checked (class methods are not).

## Adding a check for other stacks (`strength: cmd`)

Teams on other stacks can add their own check: write a command that exits 1 when it finds a weak test, then configure it in pod.yml.

```
strength: cmd
strength_cmd: node scripts/strength.js
```

Guidelines for the check command:
1. Use the same principle as the Python check: make the code return empty values and see which tests still pass.
   For example, use the stack's mutation testing tool (Stryker for JavaScript or TypeScript, go-mutesting for Go)
   and set a threshold for how many surviving mutants count as a failure.
2. Print one line per test in the form `WEAK <test id>`, so auto-merge-check can name the tests in its reasons.
3. Exit 0 when no weak test is found, and exit 1 when one is.
4. The command must not use the network and must run in CI.
5. When the command is ready, change `strength: off` to `strength: cmd` through a change with escalation,
   because pod.yml is in `docs/risk-paths`.

Until a check command exists, use `strength: off` and have the reviewer check for the 5 kinds above in review.md.
