---
name: arena
description: Settle a contested design by building two approaches side by side in separate git worktrees against the same locked tests, then compare them on tests, test strength, diff size and reviewer findings. SuperDev picks; the choice and reason go to plan.md under Decision log. Use when the user says "arena", "try both designs", "compare two approaches", "can't decide between two designs", "ลองสองแบบ", "เทียบสองแนวทาง", "ตัดสินใจไม่ได้ว่าจะออกแบบแบบไหน".
---

# Arena: compare two approaches by building both (SuperDev: SA)

Use this when there are two design approaches that can both be argued for, and building them settles it better than debate.
The human SuperDev chooses. The agent's job is to gather the evidence.

## Before you start
1. Gate 3 has passed, and the change's tests are committed on `change/NNN` and locked.
2. Describe approach A and approach B in 2-3 lines each. Ask the human to confirm they are genuinely different.

## Steps
1. Ask the human to create the worktrees and lock the tests in both:
   ```
   git worktree add ../arena-a -b change/NNN-arena-a change/NNN
   git worktree add ../arena-b -b change/NNN-arena-b change/NNN
   mkdir -p ../arena-a/.pod ../arena-b/.pod
   touch ../arena-a/.pod/lock-tests ../arena-b/.pod/lock-tests
   ```
2. Run two agents in parallel, one per worktree, each using `/superdev:build`.
   Both get the same locked tests and only the description of their own approach.
3. When both finish, collect the results in each worktree:
   - Does `make test` pass?
   - Does `scripts/test-strength.sh` pass?
   - Diff size: `git diff --shortstat change/NNN...HEAD`
   - `reviewer` agent findings: number of Blocker, Major, Minor
4. Build a comparison table for the human:

   | Criterion | A | B |
   |---|---|---|
   | make test | | |
   | test-strength | | |
   | diff (lines) | | |
   | Blocker / Major / Minor | | |

5. The human SuperDev chooses. If the results are close, recommend the one with the smaller, more readable diff.
6. Record the decision in plan.md:
   ```
   ## Decision log
   - <date> arena: chose A (<approach>) over B (<approach>) because <reason from the table>
   ```
   Editing plan.md makes the gate 3 approvals stale. Tell SuperDev and SuperBiz to sign again.
7. Bring the winner into `change/NNN`, then ask the human to delete the loser:
   ```
   git switch change/NNN && git merge change/NNN-arena-a
   git worktree remove ../arena-a && git worktree remove ../arena-b
   git branch -D change/NNN-arena-b && git branch -d change/NNN-arena-a
   ```

## Do not
- Choose on the human's behalf, or combine the two approaches without a decision.
- Edit the locked tests in either approach to make it pass.

## When done
Tell the human to sign gate 3 again, then continue with `/superdev:review`.
