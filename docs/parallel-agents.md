# Running several agents in parallel

Principle: run in parallel only the work that can be split. Every stream reports back to each person's main session, and people decide at the gates.

## 3 rules

| Work | How | Why |
|---|---|---|
| Read-only agents (ba-researcher, ux-critic, reviewer) | Always safe to run in parallel | They do not edit files, so they cannot collide |
| Agents that write code | One agent per worktree, with no overlapping files | If plan.md cannot split the files, do the parts one at a time |
| Planning, writing the spec and approving gates | A single main session | Sequential work gets worse with several agents |

## Start from plan.md

The split must be written in plan.md before gate 3, and gate 3 checks this format:

```
## Throughput checkpoint
- Blocking first steps: failing tests and the structures in Data shape
- Independent workstreams: list page (A) and detail page (B)
- Shared mutable state: n/a: each part edits its own files
- Smallest safe decomposition: one requirement per commit

## Parallel parts
### A
files: app/history.py
### B
files: app/detail.py
```

- If the work is not split, write `none: <reason>` under `## Parallel parts`.
- Each part's files must not overlap. If they do, gate 3 fails and names the duplicated files.
- If there is shared mutable state, first separate it into files owned by each part. If that is not possible, do those parts one at a time.
- Build each part with `/superdev:build`, one unit at a time, and commit every unit whose tests pass.

## SuperBiz: fan out in one session

In Claude Code with `plugins/superbiz` loaded:

```
/superbiz:spec docs/changes/002-[change-name]
Run ba-researcher and ux-critic in parallel, then merge their results into spec.md
```

## SuperDev: build two parts in parallel, then review from three angles

Before starting, plan.md must split the work into parts A and B that edit non-overlapping files, and the change's tests must already be committed on `change/001`.

```
git worktree add ../pod-a -b change/001-a change/001
git worktree add ../pod-b -b change/001-b change/001
mkdir -p ../pod-a/.pod ../pod-b/.pod
touch ../pod-a/.pod/lock-tests ../pod-b/.pod/lock-tests

# terminal 1
cd ../pod-a && claude --plugin-dir ~/my-pod/plugins/superdev
# terminal 2
cd ../pod-b && claude --plugin-dir ~/my-pod/plugins/superdev

# merge, then let the locked tests decide
git switch change/001
git merge change/001-a change/001-b
make check

# three-angle review in parallel, followed by reviewer-second (a different model) as a second opinion
/superdev:review

# clean up
git worktree remove ../pod-a && git worktree remove ../pod-b
```

## Arena: when the design approach is still undecided

Use two worktrees the same way, but both do the same work with different approaches. Compare them with the locked tests,
test strength, diff size and the reviewer results. SuperDev chooses and records the decision in plan.md under `## Decision log`.
The steps are in the `/superdev:arena` skill.

## Cautions

- `.pod/` is not part of a new git worktree, so its tests are not locked yet. Run `touch .pod/lock-tests` in every worktree.
- The kill switch works per folder. To stop every agent, run `touch .pod/kill-switch` in every worktree.
- A merge conflict means the file split in plan.md was not real. Fix plan.md, then do the conflicting parts one at a time.
- Do not run more code-writing agents at once than SuperDev can review. Two parts are usually enough.
