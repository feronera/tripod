---
name: test-first
description: Write failing tests from the spec edge cases that observe real behavior, check them with scripts/test-strength.sh, commit them and lock tests with .pod/lock-tests, then hand over to the build skill. Use when the user says "เริ่มเขียนโค้ด", "เขียน test ก่อน", "test first", "TDD", "implement the plan".
---

# Test-first (SuperDev: Dev and QA)

Goal: tests that fail for the right reason, check real behavior, and are locked before any code is written.

## Steps
1. Check that gate 3 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 3`.
   If it fails, tell the human and stop.
2. Read spec.md (Requirements and Edge cases) and plan.md (Data shape and Order of work).
3. Write tests in `tests_dir` from pod.yml (default `tests/`, with unittest), covering every requirement and every edge case.
   Name each test after its R or E, for example `test_r1_...`, `test_e2_...`.
4. Each test must call the code the way a user does, and assert the result against an explicit value.
   Avoid the 5 kinds of weak test, which still pass when every function in `code_dirs` (default `app/`) returns None. See `docs/test-strength.md`.
   - Weak or missing assertion: for example only `assertTrue(x)` or `assertIsNotNone(x)`.
   - Checks only a mock or the absence of data: for example only `assertIsNone(...)` or `assertEqual(..., [])`.
     Pair it with a case that has data in the same test.
   - Self-referential: the expected value comes from the code under test, for example `assertEqual(f(a), f(a))`.
   - Pinned constant: asserts a constant or config value copied from the code instead of testing the mechanism that uses it.
   - Fixture checks fixture: asserts data the test built itself without calling the code under test.
5. Run `make test` and confirm the new tests fail for the right reason (not an import error or a typo).
6. Run `scripts/test-strength.sh` before locking. (If pod.yml sets `strength: off`, check the 5 kinds above yourself and record it in review.md.)
   - `WEAK <test id>`: fix the test as suggested, then run again until there is no WEAK.
   - `FAIL (normal run) <test id>`: a test that is still red cannot be measured yet. Check it yourself against the 5 kinds above.
     `make check` checks again when the code is done. If a weak test is found after locking, stop and tell the human.
7. Show the list of tests to the human. Once the human confirms, commit:
   `git add <tests_dir> && git commit -m "test(NNN): failing tests from spec"`.
8. Ask the human to lock the tests: `touch .pod/lock-tests`.
   From then on, the protect-tests hook refuses edits to files in `tests_dir`.

## Do not
- Write code in `code_dirs` in this skill.
- Add dependencies that the project's AGENTS.md does not allow.
- Delete `.pod/lock-tests` yourself.

## When done
Tell the human the next step is `/superdev:build`, and that after the change is finished they unlock with `rm .pod/lock-tests`.
