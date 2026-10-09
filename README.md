# Tripod

An agentic delivery practice for small teams. Agents draft the work of every role; a few accountable people make the decisions at defined gates, and the rules that matter are enforced by scripts, hooks and CI rather than by memory.

Tripod packages that practice as two Claude Code plugins, a set of gate scripts, document templates and a CI workflow. Install it into a new project or an existing repository of any stack.

![One change through the loop: eight steps from intent to release, four gates signed by people, and incidents that start the next change](docs/images/adlc-loop.svg)

## The three legs

| Role | Covers | Decides | Status |
|---|---|---|---|
| **SuperBiz** | PO, PM, BA, Designer | What to build and why | Available. One or more people |
| **SuperDev** | SA, Dev, QA, Deploy, Maintenance | How to build it, and whether it is safe | Available. One or more people |
| **SuperCEO** | Direction, priorities, high-risk approvals across a tribe | Whether the risk is worth taking | Planned. The `escalation` role in `pod.yml` (one or more people) stands in today |

Two words for team size: a **pod** is one small team (SuperBiz and SuperDev, one or more of each). A **tribe** is a group of pods that share the kit and an escalation.

## How it works

Every change moves through four gates. Each gate has an owner who approves and a second person who cross-checks, so the author and the approver are never the same person.

| Gate | Artifact | Owner approves | Cross-check |
|---|---|---|---|
| 1 | `intent.md` | SuperBiz | SuperDev: feasible and measurable? |
| 2 | `spec.md`, `ux-brief.md` | SuperBiz | SuperDev |
| 3 | `plan.md` | SuperDev | SuperBiz: still matches the intent? |
| 4 | Pull request, `acceptance.md` | SuperDev (code); with 2+ SuperDevs, one who did not write it | SuperBiz: accepted against the success measure |

### Where people are in the loop

Some steps wait for a person (**HITL**, human in the loop): nothing moves until someone approves. Others run on their own while a person watches and can stop them (**HOTL**, human on the loop). Watching only works if you can see what the agents did, so every step leaves evidence in the repo.

![For each step: what the agent does, whether a person must approve (HITL) or watches and can stop it (HOTL), and where to see the evidence](docs/images/hitl-hotl.svg)

### Guardrails

- **Risk tiers.** Each intent declares `Risk: low | medium | high`. High-risk changes need an additional escalation approval at gates 2 and 4. Touching any path in `docs/risk-paths` raises a change to high, and risk can only go up.
- **Stale approvals.** Every approval records the artifact's blob hash. Editing an artifact after approval invalidates the approval.
- **WIP limit.** No more than `wip_limit` changes (default 2) may be open between gate 1 and gate 4.
- **Merge by risk.** Gate 4 is split into merge-ready and release-ready.
  - Low-risk changes may be merged by the agent once nine automated conditions pass.
  - Medium-risk changes need SuperDev's approval (with 2+ SuperDevs, from one who did not write the code).
  - High-risk changes need all three approvers and a human merge.
  - Auto-merge is off by default and is unlocked by a track record of clean changes.
- **Verified identity.** CI checks pull request approvals on GitHub against the people listed in `pod.yml`.

![Who merges at each risk tier: the agent for low, the agent after SuperDev signs for medium, a person for high](docs/images/risk-lanes.svg)

The kit has three layers:

1. **Governance.** Gates, cross-approval, risk tiers, the WIP limit, and an audit trail in each change's `gates.log`.
2. **Engineering method.** Adapted from pstack (see [Credits](#credits)):
   - Model the data shape before writing logic.
   - Write a throughput checkpoint before splitting work.
   - Work in small verifiable units.
   - Test behavior, not implementation.
   - Fix bugs at the root cause.
   - Get a second opinion from a different model.
   - Run a design bake-off when the approach is contested.
3. **Enforcement.** The principles that matter are checked by scripts, hooks and CI, not left as guidance.

## Team setups

The same loop works for one pod or many. What changes is who signs, who reviews whom, and where the work queues.

### Pod of 2: one SuperBiz, one SuperDev

The starting point. Each person owns two gates and cross-checks the other two.

![Pod of two: one SuperBiz and one SuperDev share one repo; each owns two gates and cross-checks the other two](docs/images/setup-2.svg)

### Pod of 3: one SuperBiz, two SuperDevs

Every role in `pod.yml` accepts a comma-separated list. With two SuperDevs, parallel parts can be built at the same time in separate worktrees, and the SuperDev who signs gate 4 must not be the one who wrote the code.

![Pod of three: one SuperBiz and two SuperDevs build parallel parts; the gate 4 owner is the SuperDev who did not write the code](docs/images/setup-3.svg)

### Tribe: N pods, one kit

SuperBiz owns or cross-checks every gate, so keep to about 3 SuperDevs per SuperBiz. Beyond that, add a SuperBiz or split into two pods. Pods that share the kit and an escalation form a tribe.

![Many pods install the same versioned kit, share an escalation for high-risk work, and feed lessons back into the kit](docs/images/setup-n.svg)

When to grow, when to split, and how to size the WIP limit: [docs/scaling.md](docs/scaling.md).

## Quick start

Requirements: Python 3.10 or later, git, make and Claude Code. No other packages are needed.

### New project

```bash
git clone https://github.com/feronera/tripod ~/tripod
mkdir my-pod && cd my-pod && git init
~/tripod/scripts/pod-install.sh . --with-sample   # leave out --with-sample for an empty project
# Edit pod.yml: names, emails (must match each person's git config user.email) and GitHub logins
scripts/sync-codeowners.sh
make setup
make check
git add -A && git commit -m "chore: start pod"
```

This repository is itself a pod: Tripod is built with Tripod, and its own changes are in `docs/changes/`. That is why new projects start from the installer, which copies only the kit, rather than from a copy of this repository.

### Existing project

The installer works with any stack. It never overwrites `Makefile`, `AGENTS.md` or `CLAUDE.md`, and it can be re-run safely.

```bash
gh repo clone feronera/tripod ~/tripod
cd ~/my-project && ~/tripod/scripts/pod-install.sh .
```

The installer detects Node, Python and Go projects, pre-fills the stack settings in `pod.yml` (`test_cmd`, `code_dirs`, `tests_dir`, `strength`), and prints the remaining steps. The full adoption guide, with a checklist, is in [docs/adopt.md](docs/adopt.md).

### Plugins

Each person installs the plugin for their role:

```
/plugin marketplace add feronera/tripod
/plugin install superbiz@tripod     # or superdev@tripod
```

To try a plugin for one session without changing any settings, load it from a checkout:

```bash
claude --plugin-dir ./plugins/superbiz   # SuperBiz
claude --plugin-dir ./plugins/superdev   # SuperDev
```

In projects without a `pod.yml`, the plugin hooks allow every action and print a one-line notice.

## A change, end to end

1. **SuperBiz** starts the change with `scripts/new-change.sh order-history` and drafts the intent with `/superbiz:intent`.
2. **Gate 1.** SuperBiz signs with `scripts/gate.sh docs/changes/001-order-history 1`. SuperDev reviews the intent and runs the same command.
3. **SuperBiz** writes the UX brief and spec with `/superbiz:ux-brief` and `/superbiz:spec`. Both sign gate 2.
4. **SuperDev** writes the plan with `/superdev:plan`, covering the data shape, throughput checkpoint and parallel parts. Both sign gate 3.
5. **SuperDev** writes tests first with `/superdev:test-first`, then builds with `/superdev:build` and reviews with `/superdev:review`, and opens a pull request.
6. **SuperDev** merges according to risk with `/superdev:merge`.
7. **SuperBiz** accepts the change with `/superbiz:acceptance` and signs gate 4. Depending on risk, acceptance happens before or after the merge.
8. **SuperDev** releases with `/superdev:release` once `scripts/release-check.sh` passes, and SuperBiz publishes notes with `/superbiz:release-notes`.

Use `/superdev:bug-fix` for defects and `/superdev:arena` when two designs need to be compared.

A real run of one change through all four gates, with a merged pull request, CI, approvals, agent replies and costs: [feronera/tripod-example](https://github.com/feronera/tripod-example).

## Plugins

| Plugin | Skills | Agents | Hooks |
|---|---|---|---|
| `superbiz` | intent, ux-brief, spec, acceptance, release-notes | ba-researcher, ux-critic | biz-scope: SuperBiz edits `docs/` only |
| `superdev` | plan, test-first, build, review, bug-fix, arena, merge, release, incident | reviewer, reviewer-second, monitor | kill-switch, protect-tests, gate-guard |

## Commands

| Command | Purpose |
|---|---|
| `make setup` | Check required tools and create the local `.pod/` folder |
| `make test` | Run `test_cmd` from `pod.yml` |
| `make strength` | Find weak tests, per the `strength` mode in `pod.yml` (see [docs/test-strength.md](docs/test-strength.md)) |
| `make check` | Tests, test strength, the CODEOWNERS check and `gate-check --all`. CI runs this on every pull request |
| `make metrics CHANGE=<dir>` | Time from the first intent commit to each gate, and the total lead time |
| `scripts/new-change.sh <slug>` | Create `docs/changes/NNN-slug/intent.md`. Refused when the WIP limit is reached |
| `scripts/gate.sh <dir> <1-4>` | Sign a gate as the current `git config user.email` and record it in `gates.log` |
| `scripts/gate-check.sh <dir> [gate]` | Check one change's gates. Gate 4 means merge-ready for the change's risk |
| `scripts/gate-check.sh --all` | Check every change. A change with no `gates.log` is treated as a draft |
| `scripts/release-check.sh <dir>` | Release-ready: all gate 4 approvals present and current, no revert, and acceptance within the deadline |
| `scripts/auto-merge-check.sh <dir> [--base main] [--record]` | `ALLOW` or `DENY`, with reasons, for an automated merge. `--record` logs the automated approval |
| `scripts/mark-revert.sh <dir> "<reason>"` | Record that a change was reverted. Humans only |
| `scripts/pr-check.sh` | CI: check GitHub approvals against the change's effective risk |
| `scripts/sync-codeowners.sh [--check]` | Generate or verify `.github/CODEOWNERS` from `docs/risk-paths` |
| `scripts/parallel-check.sh <dir> [--run]` | Before splitting into parallel worktrees: each part's tests exist and import only that part's files. With `--run` after the build: each part's tests pass without the other parts' code |
| `scripts/setup-github.sh <owner/repo> [--yes]` | Enable auto-merge and protect `main`. Prints the plan; applies it only with `--yes` |
| `scripts/pod-install.sh <repo> [--with-sample] [--vendor-plugins] [--force]` | Install Tripod into another repository |
| `touch .pod/lock-tests` | Lock the tests so agents cannot edit them |
| `touch .pod/kill-switch` | Stop every agent that has the `superdev` plugin loaded |

## Repository layout

```
AGENTS.md, CLAUDE.md     Rules for every agent working in the repository
pod.yml                  Team members (lists allowed), GitHub logins, WIP limit, auto-merge and stack settings
pod.mk, Makefile         Make targets (the Makefile includes pod.mk)
plugins/                 The superbiz and superdev Claude Code plugins
scripts/                 Gate, merge, metrics and installer scripts
docs/                    Gates, risk tiers, risk paths, merge by risk, test strength,
                         parallel agents, scaling, pod charter, adoption guide, credits
docs/images/             The diagrams used in this README
docs/templates/          intent, ux-brief, spec, plan, review and acceptance templates
docs/changes/            One folder per change (NNN-slug/)
app/, tests/, logs/      Sample order-status service, its tests and a synthetic incident log
.github/                 CI workflow (pod-gates) and the generated CODEOWNERS
```

## Operating notes

- Agents never sign gates. Only humans run `scripts/gate.sh` and `scripts/mark-revert.sh`.
- An agent may run `scripts/auto-merge-check.sh --record` followed by `gh pr merge --auto --squash` only when the check returns `ALLOW`.
- `auto_merge` starts as `off`. Switch it to `low` once the team has the track record described in `docs/pod-charter.md`.
- On GitHub, a pull request cannot be approved by its author. If the agent opens pull requests with SuperDev's account, SuperBiz's approval is required instead, unless the pod has another SuperDev who did not write the code. See `docs/merge-by-risk.md`.
- The `.pod/` folder holds per-machine state and is never committed.
- All data in `app/` and `logs/` is synthetic.

## License

MIT. See [LICENSE](LICENSE).

## Credits

Several engineering methods are adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan, used under the MIT License (Copyright (c) 2026 Lauren Tan). The adapted ideas are listed in [docs/credits.md](docs/credits.md).
