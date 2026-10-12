# Adopting Tripod in an existing project

How to bring Tripod into a project that already exists, on any stack. Follow the steps in order, then confirm with the checklist.

## 1. Assess whether the project fits

A pod fits work that:
- splits into small changes, each deliverable within a few days;
- has one business decision-maker (SuperBiz) and one technical owner (SuperDev) who work together every day ([scaling.md](scaling.md) covers more people);
- has automated tests, or is ready to write tests before code;
- can be undone, for example by a revert.

Send work to a full team instead when it needs joint decisions across teams, is a large or irreversible data migration, touches security, authentication, money or personal data without specialist review, or is research with an unknown outcome. In between, start with low-risk work and mark anything from this list `Risk: high`.

## 2. Install

Run the commands in the README's [Install](../README.md#install) section, using `pod-install.sh .` inside your repository. The installer does not use the network. Options:
- `--with-sample`: copies the sample app (`app/`, `tests/test_orders.py`, `logs/`), for training repositories. All its data is invented.
- `--vendor-plugins`: copies `plugins/` into the repository, for teams that do not install plugins from GitHub. Then use `claude --plugin-dir ./plugins/superdev`.
- `--force`: overwrites existing files, keeping the old version as `<file>.pod-bak`.

It installs `pod.yml`, `pod.mk`, `scripts/`, the rule docs in `docs/` (including `docs/risk-paths` and the templates), `docs/changes/` and the CI workflow `.github/workflows/pod-gates.yml`. Rules:
- `Makefile`, `AGENTS.md` and `CLAUDE.md` are never overwritten. A Makefile is created only if none exists. `AGENTS.md` gets a `<!-- pod:begin -->` to `<!-- pod:end -->` section, and `CLAUDE.md` an `@AGENTS.md` line.
- With an existing Makefile, the installer prints an `include pod.mk` line to add. Without it, run `make -f pod.mk pod-<target>`.
- Other files that differ from the kit are skipped and listed, unless you use `--force`.
- It is safe to re-run.

Make targets: `make setup` checks the tools and creates `.pod/` (per-machine state such as the test lock and kill switch, never committed); `make test` runs `test_cmd`; `make strength` finds weak tests ([test-strength.md](test-strength.md)); `make check` runs all of these plus the CODEOWNERS check and `gate-check --all`; `make metrics CHANGE=<dir>` shows the time to each gate.

## 3. Configure

1. Edit `pod.yml`:
   - names, emails (each must match that person's `git config user.email`) and GitHub logins for SuperBiz, SuperDev and escalation;
   - several people in a role: comma-separated lists aligned by position ([scaling.md](scaling.md));
   - `base_branch` (default `main`);
   - the stack, which the installer fills in. Check it:

     | Stack | `test_cmd` | `code_dirs` | `strength` |
     |---|---|---|---|
     | Node (package.json) | `npm test` | `src` | `off` |
     | Python | `python3 -m unittest discover -s tests -t . -v` | top-level package, or `src` | `python` |
     | Go (go.mod) | `go test ./...` | `.` | `off` |
     | Unknown | Python defaults, with a warning | | |

   - `tests_dir` is `tests` (Node: `tests`, `__tests__` or `test`, whichever exists). When no tests run (exit 5), it counts as a pass only while `docs/changes/` is empty. `strength: off` makes auto-merge-check always DENY.
2. Edit `docs/risk-paths` to list the project's sensitive paths, then run `scripts/sync-codeowners.sh`.
3. Run `make -f pod.mk pod-setup` and `make -f pod.mk pod-check`. It must pass.
4. Projects not written in Python: add a step that installs the stack to `pod-gates.yml`, before `pod-check`.
5. Run `scripts/setup-github.sh <owner/repo>`, read the plan, then run it with `--yes`. It enables auto-merge and protects the main branch (the `pod-gates` check and code-owner review are required). Branch protection needs a public repository or a paid plan.
6. Fill in [pod-charter.md](pod-charter.md) together, then commit everything through a pull request.

## 4. Install the plugins (each person)

```text
/plugin marketplace add feronera/tripod
/plugin install superbiz@tripod     # SuperBiz
/plugin install superdev@tripod     # SuperDev
/plugin install superceo@tripod     # optional: priorities and briefs
```

| Plugin | Skills | Hooks |
|---|---|---|
| `superbiz` | intent, ux-brief, spec, acceptance, release-notes | biz-scope (SuperBiz edits `docs/` only), activity |
| `superdev` | plan, test-first, build, review, bug-fix, arena, merge, release, incident (agents: reviewer, reviewer-second, monitor) | kill-switch, protect-tests, gate-guard, activity |
| `superceo` | priorities, brief | none |

The repository is public, so no access request is needed. The hooks allow everything in a project without `pod.yml`, and print a one-line notice. Update with `/plugin marketplace update tripod`.

## 5. Run a pilot change

Pick `Risk: low` work that touches no path in `docs/risk-paths` and fits in one or two days. Keep `auto_merge: off`. Walk through all four gates as in the README's [end-to-end table](../README.md#a-change-end-to-end), and note what was unclear for step 8.

## 6. The trust ladder

When to enable `auto_merge: low` is in [pod-charter.md](pod-charter.md#auto-merge-trust-ladder). Auto-merge also needs `strength` set to `python` or `cmd`, CI on every pull request, and branch protection.

## 7. Measure at 30, 60 and 90 days

Run `scripts/metrics.sh docs/changes/NNN-slug` on every closed change, and `scripts/activity.sh` for agent cost ([activity-log.md](activity-log.md)). Watch:
- lead time from intent to gate 4;
- waiting time at each gate (fix the slowest first);
- changes closed;
- reverts (`event=revert` in gates.log);
- the share merged automatically (`role=auto`).

Record decisions in `docs/pod-charter.md`.

## 8. Make the kit your own

- A rule broken twice moves from a skill into a hook, script or CI check. Record it in the charter.
- Team rules go in `AGENTS.md`, outside the `pod:begin` to `pod:end` section.
- After changing a plugin, bump `version` in its `plugin.json` and `metadata.version` in `.claude-plugin/marketplace.json`, then run `claude plugin validate --strict`.

## 9. Update the kit from upstream

```bash
cd ~/tripod && git pull
cd ~/my-project && git switch -c chore/pod-kit-update
~/tripod/scripts/pod-install.sh .
git status && git diff
```

- Matching files do not change. The pod section in `AGENTS.md` is replaced.
- Files your team edited are skipped and listed. Compare each with `diff ~/tripod/<file> <file>`, then merge by hand or use `--force`. After `--force`, review every `.pod-bak` file and delete them before committing.
- `pod.yml` is not changed. A new key uses its default until you add it.
- An update touches `scripts/**` and `.github/**`, so it is a high-risk change.

## Checklist

- [ ] The project fits a pod, and the work that goes to a full team is defined
- [ ] `pod-install.sh` has run, and the skipped files are reviewed
- [ ] The Makefile includes `pod.mk`, or the team uses `make -f pod.mk`
- [ ] `pod.yml` names, emails, GitHub logins and stack are correct
- [ ] `docs/risk-paths` matches the sensitive paths, and `.github/CODEOWNERS` is committed
- [ ] `make -f pod.mk pod-check` passes locally and in CI (CI installs the stack)
- [ ] `scripts/setup-github.sh <owner/repo> --yes` has run
- [ ] `docs/pod-charter.md` is complete, and each person has installed their plugin
- [ ] The first `Risk: low` change passed all four gates with `auto_merge: off`
- [ ] Review dates are set for 30, 60 and 90 days
