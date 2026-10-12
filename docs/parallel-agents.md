# Running several agents in parallel

Run in parallel only work that can be split. Every stream reports back to each person's main session, and people decide at the gates.

| Work | How | Why |
|---|---|---|
| Read-only agents (ba-researcher, ux-critic, reviewer) | Always safe in parallel | They do not edit files, so they cannot collide |
| Agents that write code | One agent per worktree, with no overlapping files | If plan.md cannot split the files, do the parts one at a time |
| Planning, writing the spec and approving gates | A single main session | Sequential work gets worse with several agents |

## Start from plan.md

The split is written in plan.md before gate 3, and gate 3 checks this format:

```
## Throughput checkpoint
- Blocking first steps: failing tests and the structures in Data shape
- Independent workstreams: list page (A) and detail page (B)
- Shared mutable state: n/a: each part edits its own files
- Smallest safe decomposition: one requirement per commit

## Parallel parts
### A
files: app/history.py
tests: tests/test_history.py
### B
files: app/detail.py
tests: tests/test_detail.py
```

- If the work is not split, write `none: <reason>` under `## Parallel parts`.
- Parts may not share files or test files; gate 3 fails and names them. A part may add `owner: <email>` ([scaling.md](scaling.md#parallel-parts-across-superdevs)).
- Shared mutable state is split into files owned by each part first. If that is not possible, do those parts one at a time.
- After the tests are written, run `scripts/parallel-check.sh docs/changes/NNN-slug`. It fails when a part's tests import a file another part builds; build that shared interface first. It sees only direct imports, so name every interface between parts in the plan.
- After the build, run `scripts/parallel-check.sh docs/changes/NNN-slug --run --base main`. It runs each part's tests in a throwaway worktree where the other parts' files are as at the merge base. A part that fails depends on another: merge that one first. (In tripod-example change 003 it found that the server part needed the page part.)
- Build each part with `/superdev:build`, one unit at a time, committing every unit whose tests pass.

## SuperBiz: fan out in one session

```
/superbiz:spec docs/changes/002-[change-name]
Run ba-researcher and ux-critic in parallel, then merge their results into spec.md
```

## SuperDev: build two parts, then review from three angles

The tests must already be committed on `change/001`.

```bash
git worktree add ../pod-a -b change/001-a change/001
git worktree add ../pod-b -b change/001-b change/001
mkdir -p ../pod-a/.pod ../pod-b/.pod
touch ../pod-a/.pod/lock-tests ../pod-b/.pod/lock-tests
# one terminal each: cd ../pod-a (or ../pod-b) && claude --plugin-dir ~/my-pod/plugins/superdev
git switch change/001 && git merge change/001-a change/001-b && make check
/superdev:review        # three angles in parallel, then reviewer-second on a different model
git worktree remove ../pod-a && git worktree remove ../pod-b
```

**Arena**, when the design approach is undecided: two worktrees do the same work with different approaches. Compare them with the locked tests, test strength, diff size and the reviewers. SuperDev chooses and records it in plan.md under `## Decision log`. The steps are in `/superdev:arena`.

## Cautions

- `.pod/` is not part of a new worktree: run `touch .pod/lock-tests` in each one. The kill switch also works per folder, so touch it in every worktree to stop every agent.
- A merge conflict means the file split was not real. Fix plan.md and do those parts one at a time.
- Do not run more code-writing agents than the SuperDevs can review. Two parts are usually enough.
