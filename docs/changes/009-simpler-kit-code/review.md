blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: d9d1cbb14a23fac1232c5982c4161d2530bbd9d9

# Review: Simpler kit code

## Checks against the spec
| Req | Result |
|---|---|
| R1 dead code | Removed: the 17 lines after `return entries` in `parse_log`, left by change 007 |
| R2 one git helper | `subprocess.run(["git"…])` appears only in `lib.git_out`. It now takes `cwd`, `text` and `env`, and returns 127 when git is missing. `loop.git` and `merge_rules.git` are now one-line calls to it, kept as names because they are used at 22 call sites |
| R3 one show-at-ref | `lib.show(ref, path, root)` returns bytes or None. Used by `known_changes`, `plan_merged_as_is`, `mode_record_on_base`, `sponsor.change_logs`, `superceo.branch_file` and `loop.base_rules` |
| R4 one trusted base | `lib.trusted_base(cfg, root)`. Used by peer review, the mode record, the plan skip, sponsor spend, the loop and agent-sign. `base_problem` is still called directly only by `pod_config_problems` |
| R5 one risk-paths parser | `parse_risk_paths(text)`; `read_risk_paths` and the loop use it |
| R6 installer | The Commands section comes from AGENTS.md. AGENTS.md now also lists `agent-sign` and `digest`, which only the installer's copy had |
| R7 default base | `auto-merge-check.sh` and `parallel-check.sh --run` default to the trusted base. An untrusted base gives one DENY reason, or `Refused:` for parallel-check (`tests/test_simpler_kit.py`, failing before the fix with "cannot compare with base 'main'") |
| R8 merge rules in one doc | AGENTS.md, the gate-guard comment and the merge skill point to docs/merge-by-risk.md. The skill drops `--base origin/main` and the manual risk-path check, and keeps `git fetch origin`. `--base main` is gone from every doc and usage line |
| R9 versions | Plugins and marketplace are at 1.0.1. `claude plugin validate --strict` passes for all four manifests |
| R10 size (amended) | 4,478 to 4,447 lines. The survey's estimate of about 100 lines was too high; see the spec amendment |

## Second opinion (Sonnet 5.5, independent)
- blockers_found 0, verdict agree.
- Checked clean:
  - `git status --porcelain` is read as bytes, so the first column is kept;
  - every caller of `merge_rules.git` already stripped its output;
  - git-missing fallbacks behave as before;
  - None-base handling is safe;
  - pod_install imports lib from any working directory;
  - R7 tests fail on the old code.

| Finding | Severity | Outcome |
|---|---|---|
| The installed AGENTS.md strength line said "app/", which is wrong in other repositories | Low | Fixed: "the code folders" |
| A dead local `import lib` in activity.py, with a misleading comment (lib was already imported at the top) | Low | Fixed: removed |
| docs/parallel-agents.md still said `--run --base main` | Low | Fixed |
| superceo and sponsor now decode bytes, so CRLF is no longer turned into LF | Very low | Accepted: sponsor splits lines; SuperCEO prompt text only |
| Import order in pod_install.py | Cosmetic | Fixed |

## Test edits (PO approved on 2026-10-13)
- `tests/test_simpler_kit.py` is new and was locked at its commit.
- `tests/test_pod_v3.py`: the two version assertions changed from 1.0.0 to 1.0.1. No other test changed.

## Gates
Gates 2 and 3 were signed again after the R10 and R8 amendments. On 2026-10-13 the PO asked the agent to run those signatures ("จัดการให้หน่อย", "handle it for me").

## Checks
- `make check`: pass (412 tests, test strength, CODEOWNERS, gate-check)

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
