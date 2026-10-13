# Spec: Simpler kit code

References: intent.md, ux-brief.md

Amended on 2026-10-13 after the build, with the PO's decision. R10's line target came from the survey's estimate, which was too high. The shared helpers carry the docstrings and error handling that each copy used to repeat, so removing six copies saved fewer lines than estimated. R10 now records the measured result. The intent's line measure (4,350 or fewer) is reported as not met in acceptance.md. Its other measures (one place per job) are met.

## Requirements
Removals with no behavior change
- R1: The unreachable code after `return entries` in `lib.parse_log` must be removed. (verified by: review; `make check`)
- R2: Every git call in scripts/ must go through one helper in lib.py. `merge_rules.git`, `loop.git` and the raw `subprocess.run(["git", …])` calls are replaced. The helper keeps today's options: text or bytes, stripped or not, and `core.quotePath=false` where the loop needs it. (verified by: `grep -n 'subprocess.run(\["git"' scripts/` finds only the helper; `make check`)
- R3: Reading a file at a ref (`git show <ref>:<path>`) must go through one helper, `lib.show(ref, path, root)`. It returns the file's bytes, or None when the file or the ref does not exist. (verified by: grep; `make check`)
- R4: The trusted base must come from one helper, `lib.trusted_base(cfg, root)`. It returns `(ref, problem)`, built from `base_problem` and `resolve_base`. Every caller that pairs them today uses it. (verified by: grep; existing `test_trusted_base*` unchanged)
- R5: docs/risk-paths text must be parsed by one function, which the loop also uses. (verified by: grep; `make check`)
- R6: The installer must take the "Commands" section of the AGENTS.md pod block from AGENTS.md, like the other sections, and drop its hand-written copy. (verified by: existing installer tests; the installed AGENTS.md lists the same commands)

The one behavior change
- R7: `scripts/auto-merge-check.sh` and `scripts/parallel-check.sh --run` must default `--base` to the trusted base (R4) instead of `main`. An explicit `--base` still wins. `pr-check.sh` already reads the base from the pull request and is unchanged. (verified by: test)

Text
- R8: The per-risk merge rules must be written only in docs/merge-by-risk.md. AGENTS.md, the gate-guard hook comment and the merge skill point to it. The merge skill drops its `--base origin/main` arguments and its manual risk-path check, which auto-merge-check already does and reports. It keeps `git fetch origin` first, so `origin/<base>` is current. (verified by: review)
- R9: The edited merge skill bumps every plugin's `version`, and the marketplace's `metadata.version`, from 1.0.0 to 1.0.1. (verified by: `claude plugin validate --strict`; the version test)

Size
- R10: scripts/*.py must total fewer lines than before the change (4,478), with no duplication added. Measured: 4,447. (verified by: `wc -l`)

## Edge cases
- E1: No `origin/<base>`: the default base is the local branch, as `resolve_base` does today.
- E2: `base_problem` is not None (a redirected base): auto-merge-check prints DENY with that problem as a reason, and does not compare against an untrusted base.
- E3: `parallel-check.sh` without `--run` does not use a base, so it is unchanged.

## Flagged concerns
- R2 to R6 change many call sites but not behavior. The safety net is the 409 existing tests, which must pass unchanged.

## Out of scope
- SuperCEO's own branch scan, one parser for all logs, and the two timestamp formats (PO's scope choice).
- Splitting lib.py into modules. It moves lines without removing them.
