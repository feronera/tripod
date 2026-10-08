---
name: build
description: Implement an approved plan.md in small verifiable units after tests are locked. One unit is the smallest change that ends in a passing check, committed as feat(NNN) before the next unit starts. Use when the user says "build", "ลงมือเขียนโค้ด", "ทำตาม plan", "implement", "เขียนโค้ดให้ test ผ่าน".
---

# Build one unit at a time (SuperDev: Dev)

Goal: code in `app/` that makes the locked tests pass, with every commit in a checked state.

## Before you start
1. Check that gate 3 has passed: `scripts/gate-check.sh docs/changes/NNN-slug 3`.
2. Check that the tests are locked (`.pod/lock-tests` exists). If not, use `/superdev:test-first` first.
3. Read plan.md: Data shape, Throughput checkpoint, Parallel parts and Order of work.
4. If Parallel parts has more than one part, follow `docs/parallel-agents.md`
   (one agent per worktree, each editing only the files in its own part's `files:` line).
5. Check that the starting point is green: `make test` must pass every test except the new locked ones.

## What a unit is
- A unit is the smallest change that ends in a check, for example the R1 test passing.
- Start with the Blocking first steps in plan.md, for example the structures in Data shape before the logic.

## Loop, one unit at a time
1. Pick the next unit from Order of work.
2. Change only the code this unit needs. Do not edit anything outside Files to change.
3. Run the tests in the foreground and wait for the result. For speed, run only the test files this change touches
   (for example `python3 -m unittest tests.test_orders`). Confirm this unit's tests pass and every test that passed
   before still passes.
4. Commit immediately: `git commit -m "feat(NNN): <unit>"`.
5. Do not start the next unit while any test that should already pass is red. Make it green first.
6. If a unit can only pass by changing a locked test, stop immediately. Report the test, the reason and the options,
   and let the human decide. Never work around the hook by other means, such as overwriting the file with Bash.

## When every unit is done
1. Run `make check` (including `scripts/test-strength.sh`). It must pass.
2. Check that the diff stays within the scope of plan.md: `git diff main...HEAD --stat`.

## Do not
- Add dependencies outside the Python standard library.
- Combine several units in one commit, or commit while tests are red.
- Run `scripts/gate.sh` or delete `.pod/lock-tests`.
- Run commands in the background, or end your turn while a command is still running.

## When done
Tell the human the next step is `/superdev:review`.
