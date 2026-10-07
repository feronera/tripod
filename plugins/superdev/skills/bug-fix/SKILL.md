---
name: bug-fix
description: Fix a bug at its root cause. Reproduce first and show the failing behavior, ask why until the cause is in code, write a failing test that reproduces it, lock tests, fix, and prove the fix with the same reproduction. Uses the normal change flow. Use when the user says "แก้ bug", "มี bug", "ระบบทำงานผิด", "bug fix", "fix this bug".
---

# Fix a bug at the root cause (SuperDev: Dev and QA)

Goal: fix the real cause, and prove it with the same reproduction that exposed the bug.

## 1. Reproduce it first
- Find the command or steps that trigger the bug, then run them and show the wrong result.
- Record the command and its output (with personal data removed), for example:
  ```
  $ <command that triggers the bug>
  <wrong result>
  Expected: <correct result>
  ```
- If you cannot reproduce it, do not fix anything. Report what you tried and ask the human for more information.

## 2. Find the root cause
- Keep asking "why" until the answer points to a line of code (`path:line`) or to wrong data.
- Never guess. When unsure, add temporary print statements or read the actual error, and remove them before committing.
- Search for the same pattern elsewhere in the code (`grep`) and fix every place with the same cause.
- Adding `if x is None: return` to silence an error treats the symptom, not the root cause.

## 3. Use the normal change flow
1. Ask the human to run `scripts/new-change.sh <slug>`.
2. Draft intent.md: the Problem is the bug, with the reproduction command and its output. The Success measure is
   that the same command gives the correct result. Set Risk per `docs/risk-tiers.md`.
3. Pass gates 1 to 3 as usual. plan.md states the root cause under Data shape or Risks.

## 4. Write a test that reproduces the bug, then lock it
- Write a test that fails because of this bug and passes when it is fixed correctly (assert an explicit correct value).
- Run `make test` to confirm the test fails with the same symptom as the reproduction.
- Commit the test, then ask the human to run `touch .pod/lock-tests`.

## 5. Fix and prove
- Fix the code at the root cause, following `/superdev:build`.
- Run the reproduction command from step 1 again, and show the correct result next to the original one.
- Run `make check`.

## Do not
- Fix a symptom without knowing the root cause.
- Edit locked tests to make them pass.
- Run `scripts/gate.sh`.

## When done
Hand over to `/superdev:review`, and include the reproduction command with the before and after results in review.md.
