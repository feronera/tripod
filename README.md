# Tripod

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/feronera/tripod)](https://github.com/feronera/tripod/releases)
[![Built with Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-5B6FF5)](https://claude.com/claude-code)

**An agentic delivery practice for small teams.** Each role is a person paired with an agent: the agent drafts the work, the person makes the decision at four gates. The rules that matter are enforced by scripts, hooks and CI, not left to memory.

Tripod ships as two Claude Code plugins, gate scripts, document templates and a CI workflow, and installs into new or existing repositories on any stack.

![One change through the loop: eight steps from intent to release, four gates signed by people, and incidents that start the next change](docs/images/adlc-loop.svg)

## Why Tripod

- **Agents write faster than people can review.** The bottleneck in AI-assisted delivery is verification, not generation. Tripod puts the review where it matters: four gates, each with an owner and a cross-check.
- **Small teams can cover every role.** A SuperBiz (product, analysis, design) and a SuperDev (architecture, build, test, release, operations) are each a person working with their own agent, which drafts that role's work.
- **Rules hold because the system enforces them.** Stale approvals, risk tiers, locked tests, merge rules and kill switches are checked by code. Every decision leaves evidence in the repository.

## Contents

- [Core concepts](#core-concepts)
- [How it works](#how-it-works)
- [Team setups](#team-setups)
- [Getting started](#getting-started)
- [A change, end to end](#a-change-end-to-end)
- [Reference](#reference)
- [Safety model](#safety-model)
- [Status and roadmap](#status-and-roadmap)
- [Contributing](#contributing)
- [License and credits](#license-and-credits)

## Core concepts

Each of the three legs is a **person and an agent working as one**. The agent drafts, researches, builds and checks. The person decides, and only the person signs a gate.

| Leg | Covers | The agent | The person decides | Status |
|---|---|---|---|---|
| **SuperBiz** | PO, PM, BA, Designer | `superbiz` plugin: intent, UX brief, spec, acceptance, release notes | What to build and why | Available. One or more people |
| **SuperDev** | SA, Dev, QA, Deploy, Maintenance | `superdev` plugin: plan, tests, build, review, merge, release, incidents | How to build it, and whether it is safe | Available. One or more people |
| **SuperCEO** | Direction, priorities, high-risk approvals across a tribe | Planned `superceo` agent: tribe-wide priorities, metrics and escalation briefs | Whether the risk is worth taking | Planned. The `escalation` role in `pod.yml` stands in for the person today |

- A **pod** is one small team: one or more SuperBiz and one or more SuperDev, each with their agent.
- A **tribe** is a group of pods that share the kit and an escalation.
- A **change** is one unit of work. It lives in `docs/changes/NNN-slug/`, with every artifact and the signatures in `gates.log`.

## How it works

### Four gates

Every change passes four gates. Each gate has an owner who approves and a second person who cross-checks, so the author and the approver are never the same person.

| Gate | Artifact | Owner approves | Cross-check |
|---|---|---|---|
| 1 | `intent.md` | SuperBiz | SuperDev: feasible and measurable? |
| 2 | `spec.md`, `ux-brief.md` | SuperBiz | SuperDev |
| 3 | `plan.md` | SuperDev | SuperBiz: still matches the intent? |
| 4 | Pull request, `acceptance.md` | SuperDev (code). With 2+ SuperDevs, one who did not write it | SuperBiz: accepted against the success measure |

### Where people are in the loop

Some steps wait for a person (**HITL**, human in the loop): nothing moves until someone approves. Others run on their own while a person watches and can stop them (**HOTL**, human on the loop). Watching only works if you can see what the agents did, so every step leaves evidence in the repository.

![For each step: what the agent does, whether a person must approve (HITL) or watches and can stop it (HOTL), and where to see the evidence](docs/images/hitl-hotl.svg)

### Guardrails

| Guardrail | What it does |
|---|---|
| Risk tiers | Each intent declares `Risk: low`, `medium` or `high`. High risk adds an escalation signature at gates 2 and 4. Touching a path in `docs/risk-paths` makes a change high, and risk can only go up |
| Stale approvals | Each signature records the artifact's hash. Editing an approved artifact invalidates the approval |
| WIP limit | At most `wip_limit` changes (default 2) between gate 1 and gate 4 |
| Locked tests | Tests are written first and locked; agents cannot edit them while they build |
| Merge by risk | Gate 4 is split into merge-ready and release-ready. Who merges depends on risk (below) |
| Verified identity | CI checks GitHub approvals against the people in `pod.yml` |
| Kill switch | `touch .pod/kill-switch` stops every SuperDev agent at once |

![Who merges at each risk tier: the agent for low, the agent after SuperDev signs for medium, a person for high](docs/images/risk-lanes.svg)

### Three layers

1. **Governance.** Gates, cross-approval, risk tiers, the WIP limit and the `gates.log` audit trail.
2. **Engineering method**, adapted from pstack:
   - Model the data shape before writing logic.
   - Write a throughput checkpoint before splitting work.
   - Work in small verifiable units.
   - Test behavior, not implementation.
   - Fix bugs at the root cause.
   - Get a second opinion from a different model.
   - Run a design bake-off when the approach is contested.
3. **Enforcement.** The principles that matter are checked by scripts, hooks and CI.

## Team setups

The same loop works for one pod or many. What changes is who signs, who reviews whom, and where the work queues.

### Pod of 2: one SuperBiz, one SuperDev

The starting point. Each person owns two gates and cross-checks the other two.

![Pod of two: one SuperBiz and one SuperDev share one repo; each owns two gates and cross-checks the other two](docs/images/setup-2.svg)

### Pod of 3: one SuperBiz, two SuperDevs

Every role in `pod.yml` accepts a comma-separated list. Two SuperDevs can build parallel parts at the same time in separate worktrees. The SuperDev who signs gate 4 must not be the one who wrote the code.

![Pod of three: one SuperBiz and two SuperDevs build parallel parts; the gate 4 owner is the SuperDev who did not write the code](docs/images/setup-3.svg)

### Tribe: N pods, one kit

SuperBiz owns or cross-checks every gate, so keep to about three SuperDevs per SuperBiz. Beyond that, add a SuperBiz or split into two pods. Pods that share the kit and an escalation form a tribe.

![Many pods install the same versioned kit, share an escalation for high-risk work, and feed lessons back into the kit](docs/images/setup-n.svg)

When to grow, when to split, and how to size the WIP limit: [docs/scaling.md](docs/scaling.md).

## Getting started

**Requirements:** Python 3.10 or later, git, make and [Claude Code](https://claude.com/claude-code). No other packages are needed.

### New project

```bash
git clone https://github.com/feronera/tripod ~/tripod
mkdir my-pod && cd my-pod && git init
~/tripod/scripts/pod-install.sh . --with-sample   # leave out --with-sample for an empty project
# Edit pod.yml: names, emails (each must match that person's git config user.email) and GitHub logins
scripts/sync-codeowners.sh
make setup
make check
git add -A && git commit -m "chore: start pod"
```

### Existing project

The installer detects Node, Python and Go projects and pre-fills the stack settings in `pod.yml` (`test_cmd`, `code_dirs`, `tests_dir`, `strength`). It never overwrites `Makefile`, `AGENTS.md` or `CLAUDE.md`, and it can be re-run safely.

```bash
git clone https://github.com/feronera/tripod ~/tripod
cd ~/my-project && ~/tripod/scripts/pod-install.sh .
```

The adoption guide, with a checklist, is in [docs/adopt.md](docs/adopt.md).

### Plugins

Each person installs the plugin for their role:

```text
/plugin marketplace add feronera/tripod
/plugin install superbiz@tripod     # or superdev@tripod
```

To try a plugin for one session without changing any settings:

```bash
claude --plugin-dir ~/tripod/plugins/superbiz   # SuperBiz
claude --plugin-dir ~/tripod/plugins/superdev   # SuperDev
```

In projects without a `pod.yml`, the plugin hooks allow every action and print a one-line notice.

### Protect the main branch

```bash
scripts/setup-github.sh <owner/repo>         # prints the plan
scripts/setup-github.sh <owner/repo> --yes   # applies it
```

Branch protection requires a public repository or a paid GitHub plan.

## A change, end to end

| Step | Who | Command |
|---|---|---|
| 1. Start and draft the intent | SuperBiz | `scripts/new-change.sh <slug>`, then `/superbiz:intent` |
| Gate 1 | SuperBiz, then SuperDev | `scripts/gate.sh docs/changes/NNN-slug 1` |
| 2. UX brief and spec | SuperBiz | `/superbiz:ux-brief`, `/superbiz:spec` |
| Gate 2 | Both (+ escalation if high) | `scripts/gate.sh … 2` |
| 3. Plan | SuperDev | `/superdev:plan` |
| Gate 3 | Both | `scripts/gate.sh … 3` |
| 4. Tests first, then lock | SuperDev | `/superdev:test-first`, `touch .pod/lock-tests` |
| 5. Build and review | SuperDev | `/superdev:build`, `/superdev:review`, open a pull request |
| 6. Merge by risk | SuperDev | `/superdev:merge` |
| 7. Accept | SuperBiz | `/superbiz:acceptance`, then gate 4 |
| 8. Release | SuperDev, SuperBiz | `scripts/release-check.sh`, `/superdev:release`, `/superbiz:release-notes` |

Use `/superdev:bug-fix` for defects, `/superdev:arena` to compare two designs, and `/superdev:incident` to turn a log into the next intent.

**See it in practice:** [feronera/tripod-example](https://github.com/feronera/tripod-example) shows three real changes on GitHub with merged pull requests, CI, approvals, agent replies and costs:
- a high-risk change merged by a person
- a low-risk change merged by the agent
- a customer-facing page built by two agents in parallel

## Reference

### Plugins

| Plugin | Skills | Agents | Hooks |
|---|---|---|---|
| `superbiz` | intent, ux-brief, spec, acceptance, release-notes | ba-researcher, ux-critic | biz-scope: SuperBiz edits `docs/` only |
| `superdev` | plan, test-first, build, review, bug-fix, arena, merge, release, incident | reviewer, reviewer-second, monitor | kill-switch, protect-tests, gate-guard |

### Commands

**Everyday**

| Command | Purpose |
|---|---|
| `make setup` | Check required tools and create the local `.pod/` folder |
| `make test` | Run `test_cmd` from `pod.yml` |
| `make strength` | Find weak tests (see [docs/test-strength.md](docs/test-strength.md)) |
| `make check` | Tests, test strength, the CODEOWNERS check and `gate-check --all`. CI runs it on every pull request |
| `make metrics CHANGE=<dir>` | Time from the first signature or intent commit to each gate, and the lead time |

**Gates**

| Command | Purpose |
|---|---|
| `scripts/new-change.sh <slug>` | Create `docs/changes/NNN-slug/intent.md`. Refused at the WIP limit |
| `scripts/gate.sh <dir> <1-4>` | Sign a gate as the current `git config user.email`, recorded in `gates.log` |
| `scripts/gate-check.sh <dir> [gate]` | Check one change. Gate 4 means merge-ready for the change's risk |
| `scripts/gate-check.sh --all` | Check every change and the pod configuration |

**Merge and release**

| Command | Purpose |
|---|---|
| `scripts/auto-merge-check.sh <dir> [--base main] [--record]` | `ALLOW` or `DENY`, with reasons, for an automated merge |
| `scripts/pr-check.sh` | CI: check GitHub approvals against the change's effective risk |
| `scripts/release-check.sh <dir>` | Release-ready: approvals current, no revert, acceptance in time |
| `scripts/mark-revert.sh <dir> "<reason>"` | Record a revert. People only |

**Parallel work**

| Command | Purpose |
|---|---|
| `scripts/parallel-check.sh <dir>` | Before splitting into worktrees: each part's tests exist and import only that part's files |
| `scripts/parallel-check.sh <dir> --run` | After the build: each part's tests pass without the other parts' code, and in which order to merge |

**Setup**

| Command | Purpose |
|---|---|
| `scripts/pod-install.sh <repo> [--with-sample] [--vendor-plugins] [--force]` | Install Tripod into a repository |
| `scripts/sync-codeowners.sh [--check]` | Generate or verify `.github/CODEOWNERS` from `docs/risk-paths` |
| `scripts/setup-github.sh <owner/repo> [--yes]` | Enable auto-merge and protect `main` |

### Repository layout

```text
AGENTS.md, CLAUDE.md     Rules for every agent working in the repository
pod.yml                  This repository's own pod (Tripod is built with Tripod)
pod.mk, Makefile         Make targets (the Makefile includes pod.mk)
plugins/                 The superbiz and superdev Claude Code plugins
scripts/                 Gate, merge, metrics, parallel-check and installer scripts
docs/                    Gates, risk tiers, risk paths, merge by risk, test strength,
                         parallel agents, scaling, pod charter, adoption guide, credits
docs/templates/          Templates, including the pod.yml that new projects receive
docs/images/             The diagrams in this README
docs/changes/            One folder per change (NNN-slug/)
app/, tests/, logs/      Sample order-status service, the kit's tests and a synthetic incident log
.github/                 CI workflow (pod-gates) and the generated CODEOWNERS
```

## Safety model

- **The agent half of a leg never signs.** Only the person in each leg runs `scripts/gate.sh` and `scripts/mark-revert.sh`.
- **Agents merge only low-risk work.** They can merge only after `scripts/auto-merge-check.sh` returns `ALLOW`. Auto-merge starts off and is earned by a track record (`docs/pod-charter.md`).
- **The author never approves their own pull request.** If the agent opens pull requests with a SuperDev's account, another SuperDev or SuperBiz approves (`docs/merge-by-risk.md`).
- **Local state stays local.** `.pod/` holds per-machine state (test lock, kill switch) and is never committed.
- **Sample data is synthetic.** All data in `app/` and `logs/` is invented.

## Status and roadmap

Current release: see [Releases](https://github.com/feronera/tripod/releases).

**Verified in real runs on GitHub** ([tripod-example](https://github.com/feronera/tripod-example)):
- the four gates with cross-checks and escalation
- branch protection
- `pr-check` by risk
- agent auto-merge for low risk
- post-merge acceptance
- automatic re-run of checks after approval
- a parallel build in two worktrees

**Covered by tests, not yet run with real teams:** pods with several SuperDevs (peer review at gate 4) and revert handling on GitHub.

**Planned:**
- an agent activity log for HOTL
- cost per change in `metrics.sh`
- SuperCEO as the third leg: a `superceo` agent for tribe-wide priorities, metrics and escalation briefs, paired with the person who signs high-risk gates

## Contributing

Tripod is built with Tripod. This repository is a pod: every change goes through the four gates in `docs/changes/`, and pull requests must pass `pod-gates`. That is why new projects start from the installer, which copies only the kit, rather than from a copy of this repository.

Issues and ideas are welcome on [GitHub Issues](https://github.com/feronera/tripod/issues). Run `make check` before opening a pull request.

## License and credits

MIT. See [LICENSE](LICENSE).

Several engineering methods are adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan, used under the MIT License (Copyright (c) 2026 Lauren Tan). The adapted ideas are listed in [docs/credits.md](docs/credits.md).
