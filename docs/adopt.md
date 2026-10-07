# Adopting Tripod in an existing project

This guide explains how to bring the SuperBiz x SuperDev way of working into a project that already exists, on any stack.
Follow the 9 steps in order, and use the checklist at the end to confirm nothing is missing.

## 1. Assess whether the project fits

A pod fits work that:
- Can be split into small changes, each deliverable within a few days.
- Has one business decision-maker (SuperBiz) and one technical owner (SuperDev) who can work together every day.
- Has automated tests, or is ready to start writing tests before code.
- Can be undone when something goes wrong, e.g. a revert returns the system to its previous state.

Send this work to a full team instead of a pod:
- Work that needs joint decisions across several teams, or has many stakeholders.
- Large data migrations, or changes that cannot be reversed.
- Security, authentication, financial or personal data work that has not yet been reviewed by a specialist.
- Research where the kind of outcome is not yet known.

If a project sits somewhere in between, start with low-risk work, and always mark work from the second list as `Risk: high`.

## 2. Install

Requirements: git, Python 3.10 or later, make and Claude Code. The installer does not use the network.

```bash
gh repo clone feronera/tripod ~/tripod
cd ~/my-project                     # your existing project's repository
~/tripod/scripts/pod-install.sh .
```

Options:
- `--with-sample` copies the sample app (`app/`, `tests/test_orders.py`, `logs/`), for training repositories.
- `--vendor-plugins` copies `plugins/` into the repository (use it when the plugins are not installed from GitHub).
- `--force` overwrites existing files, keeping the old version as `<file>.pod-bak`.

Installed files:

| File | Purpose |
|---|---|
| `pod.yml` | Pod members, GitHub logins, WIP limit, auto-merge setting and the project's stack |
| `pod.mk` | The `pod-setup`, `pod-test`, `pod-strength`, `pod-check` and `pod-metrics` targets |
| `Makefile` | Created only if the project has none. It includes `pod.mk` and adds the short names setup, test and check |
| `AGENTS.md` | Appends a `<!-- pod:begin -->` to `<!-- pod:end -->` section. Existing content is not changed |
| `CLAUDE.md` | Adds an `@AGENTS.md` line, once |
| `.gitignore` | Adds `.pod/` and `!**/skills/build/` |
| `scripts/` | gate, gate-check, new-change, release-check, auto-merge-check, pr-check, test-strength and more |
| `docs/gates.md`, `docs/risk-tiers.md`, `docs/merge-by-risk.md` | Rules for gates, risk and merge rights |
| `docs/risk-paths` | Sensitive paths. A change that touches them is high risk |
| `docs/test-strength.md` | The 5 kinds of weak test and the strength settings |
| `docs/pod-charter.md` | The pod's working agreement, to fill in together before starting |
| `docs/parallel-agents.md`, `docs/credits.md` | Running several agents, and where the ideas come from |
| `docs/templates/` | Templates for intent, ux-brief, spec, plan, review and acceptance |
| `docs/changes/` | Where the pod's changes live |
| `.github/workflows/pod-gates.yml` | CI that runs `make -f pod.mk pod-check` and `scripts/pr-check.sh` |

Installer rules:
- `Makefile`, `AGENTS.md` and `CLAUDE.md` are never overwritten.
- Other existing files whose content differs from the kit are skipped and listed, unless you use `--force`.
- If the project already has a Makefile, the installer prints an `include pod.mk` line for you to add.
  If you do not add it, run targets with `make -f pod.mk <target>`.
- It is safe to re-run. A second run with nothing to change reports that there are no changes.

## 3. Configure

1. Edit `pod.yml`:
   - Names and emails for SuperBiz, SuperDev and escalation. Each email must match that person's `git config user.email`.
   - GitHub logins (`superbiz_github`, `superdev_github`, `escalation_github`).
   - Stack: the installer fills this in from the files it finds. Check it.

     | Stack | `test_cmd` | `code_dirs` | `tests_dir` | `strength` |
     |---|---|---|---|---|
     | Node (package.json) | `npm test` | `src` | `tests`, `__tests__` or `test` | `off` |
     | Python | `python3 -m unittest discover -s tests -t . -v` | top-level package, or `src` | `tests` | `python` |
     | Go (go.mod) | `go test ./...` | `.` | `tests` | `off` |
     | Unknown | Python defaults, with a warning | | | |

   - When no tests run (exit 5 from unittest and pytest), the result counts as a pass only while `docs/changes/` has no changes.
   - `strength: off` makes auto-merge-check always answer DENY. See `docs/test-strength.md`.
2. Edit `docs/risk-paths` to match the project's sensitive paths, such as payment code, authentication and migrations.
3. Run `scripts/sync-codeowners.sh` to generate `.github/CODEOWNERS`.
4. Run `make -f pod.mk pod-setup`, then `make -f pod.mk pod-check`. It must pass.
5. Projects not written in Python: add a step that installs the stack to `.github/workflows/pod-gates.yml`, before the `pod-check` step.
6. Configure GitHub: run `scripts/setup-github.sh <owner/repo>` to see the plan, then run it again with `--yes`.
   This enables auto-merge for the repository and protects the main branch (the `pod-gates` check must pass, and code owner review is required).
7. Fill in `docs/pod-charter.md` together, then commit everything through a pull request.

## 4. Install the plugins (each person)

The plugins install directly from GitHub. The kit repository is a marketplace named `tripod`.

```
/plugin marketplace add feronera/tripod
/plugin install superbiz@tripod     # on SuperBiz's machine
/plugin install superdev@tripod     # on SuperDev's machine
```

- The repository is private. Each person needs read access to it on GitHub and working git credentials
  (check with `git ls-remote https://github.com/feronera/tripod.git`).
- The plugins work on the project's files through `CLAUDE_PROJECT_DIR`. The hooks do not block anything in a project without `pod.yml`;
  they print a one-line notice that the pod kit was not found.
- Update the plugins when the kit releases a new version: `/plugin marketplace update tripod`.
- Without a permanent install: install with `--vendor-plugins`, then use `claude --plugin-dir ./plugins/superdev`.

## 5. Run a pilot change

- Pick `Risk: low` work that does not touch any path in `docs/risk-paths` and can be delivered in one or two days.
- Keep `auto_merge: off`. Every change needs a human signature before merge.
- Walk through all 4 gates as described in the kit's README: `scripts/new-change.sh <slug>`, then intent, spec, plan, test-first, build, review and acceptance.
- Note where you got stuck and which rules were unclear, so you can adjust them in step 8.

## 6. The trust ladder: when to enable `auto_merge: low`

Enable it only when all of the following hold:
- The pod has closed `auto_merge_min_track` changes (default 10) in a row without a revert.
- `strength` is `python` or `cmd` (auto-merge needs a test-strength result).
- `make -f pod.mk pod-check` passes in CI on every pull request, and branch protection is on.
- SuperBiz and SuperDev both agree, and escalation approves, because pod.yml is in `docs/risk-paths`.

If any of the most recent changes is reverted, auto-merge-check answers DENY until a new track record is built.
Medium and high changes are never merged automatically, at any step.

## 7. Measure at 30, 60 and 90 days

Run `scripts/metrics.sh docs/changes/NNN-slug` (or `make -f pod.mk pod-metrics CHANGE=...`) on every closed change.

| Metric | Source | 30 days | 60 days | 90 days |
|---|---|---|---|---|
| Lead time from intent to gate 4 | metrics.sh | Baseline | Lower | Stable |
| Waiting time at each gate | metrics.sh | Find the slowest gate | Fix that gate | |
| Number of changes closed | `docs/changes/` | | | |
| Number of reverts | `event=revert` in gates.log | | | Not increasing |
| Share of changes merged automatically | `role=auto` in gates.log | 0 | | |

Review the numbers together at each checkpoint, and record decisions in `docs/pod-charter.md`.

## 8. Make the kit your own

- A rule that is broken twice must move from guidance in a skill into a hook, script or CI check.
  Record the move in `docs/pod-charter.md`.
- Write team-specific rules in `AGENTS.md`, outside the `<!-- pod:begin -->` to `<!-- pod:end -->` section.
- When you change a plugin in the kit repository, bump `version` in `plugins/<name>/.claude-plugin/plugin.json`
  and `metadata.version` in `.claude-plugin/marketplace.json`, then run `claude plugin validate --strict`.
  Users get the new version when they run `/plugin marketplace update tripod`.

## 9. Update the kit from upstream

```bash
cd ~/tripod && git pull
cd ~/my-project && git switch -c chore/pod-kit-update
~/tripod/scripts/pod-install.sh .
git status && git diff
```

- Files that already match the kit do not change. The pod section in `AGENTS.md` is replaced with the new version.
- Files your team has edited are skipped and listed. Compare each with the kit using
  `diff ~/tripod/<file> <file>`, then decide whether to merge the changes by hand or use `--force`.
- If you use `--force`, review `git diff` and every `.pod-bak` file, then delete the `.pod-bak` files before committing.
- An existing `pod.yml` is not changed (unless you use `--force`). If the kit adds a new key, its default applies until the team adds the key.
- An update touches `scripts/**` and `.github/**`, which are in `docs/risk-paths`, so it is a high-risk change.

## Checklist

- [ ] The project's work has been assessed as a fit for a pod, and the work that goes to a full team is defined
- [ ] The kit is cloned and `pod-install.sh` has run; the list of skipped files has been reviewed
- [ ] The existing Makefile has the `include pod.mk` line, or the team has agreed to use `make -f pod.mk`
- [ ] `pod.yml`: names, emails, GitHub logins and stack are correct
- [ ] `docs/risk-paths` matches the project's sensitive paths
- [ ] `scripts/sync-codeowners.sh` has run, and `.github/CODEOWNERS` is committed
- [ ] `make -f pod.mk pod-check` passes locally and in CI
- [ ] CI installs the project's stack before `pod-check` (projects not written in Python)
- [ ] The plan from `scripts/setup-github.sh <owner/repo>` has been reviewed, and it has run with `--yes`
- [ ] `docs/pod-charter.md` is complete
- [ ] SuperBiz has installed `superbiz@tripod`, and SuperDev has installed `superdev@tripod`
- [ ] The first `Risk: low` change has passed all 4 gates with `auto_merge: off`
- [ ] Review dates are set for 30, 60 and 90 days
- [ ] The conditions for enabling `auto_merge: low`, and who may change the setting, are agreed
