# Plan: Agent seats and agent signatures (Autonomous mode for low risk)

References: intent.md, spec.md, ux-brief.md

## Data shape

1. **Seats** come from the existing gate table, so no new mapping is needed. `OWNERS[gate] = (owner leg, cross leg)`: gates 1 and 2 are (superbiz, superdev), gates 3 and 4 are (superdev, superbiz). An agent signs as `by=agent:<leg>`, and the seat's model is `cfg["<leg>_agent_model"]`.

2. **An agent signature** is a gates.log entry like a person's, with two extra fields:
   `gate=2 role=owner by=agent:superbiz model=claude-sonnet-5-5 session=<id> at=… blob=…`
   A gates.log entry is a person's signature when `by` is an email, and an agent's when it starts with `agent:`. No entry can be both.

3. **The mode of a change** is recorded once, the first time an agent signs: `event=mode mode=autonomous at=…`. `change_mode(entries, cfg)` returns that mode, else `cfg["mode"]` (C2: a pod that switches back keeps its finished changes valid).

4. **Every acceptance rule is one function:** `agent_signature_problem(cfg, change_dir, gate, role, entry, risk, mode, usage) -> problem or None`. `usage` is the set of `(session, model)` pairs read from activity.log usage records. The rules are checked in a fixed order, and each failure returns the copy from ux-brief.md:
   1. `mode == autonomous`
   2. `risk == low`
   3. `gate != 1`
   4. the leg in `by` is the leg the role needs at that gate
   5. `model == cfg[leg_agent_model]`
   6. `(session, model)` is in `usage`

   check_gate calls it for agent entries. For person entries it keeps today's email check.

5. **The agent-sign result** comes from `claude -p … --output-format json`: `{session_id, result, modelUsage}`. The verdict is the last line of `result` matching `VERDICT: APPROVE|REFUSE`. Anything else counts as REFUSE (E6). The recorded model is the seat's model, and only if `modelUsage` contains it (R7).

## Throughput checkpoint
- Blocking first steps: failing tests for R1–R14 and E1–E9 with a fake `claude` on PATH; the pod.yml keys and `agent_signature_problem` in lib.py
- Independent workstreams: docs (docs/autonomous.md, README, AGENTS.md, gates.md, merge-by-risk.md) once the copy and keys are fixed; the R15/R16 demo once agent-sign works
- Shared mutable state: `scripts/lib.py` (config, check_gate, gate_complete, metrics) is edited by every step, so steps run in order
- Smallest safe decomposition: (1) config and validation, (2) check_gate accepts agent entries, (3) agent-sign.sh with a fake claude, (4) activity and metrics signature lines, (5) docs and version, (6) demo with the real claude; each ends with `make check` passing

## Parallel parts
none: one SuperDev, and steps 2 to 4 all build on the config and check rules in scripts/lib.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `scripts/lib.py` | read `mode`, `*_agent_model`, `sponsor_*`; `pod_config_problems` for autonomous; `change_mode`, `agent_signature_problem`; check_gate and gate_complete accept agent entries; gate 1 people only; owner/cross models differ | R1–R3, R8–R11 |
| `scripts/agent_sign.py` (new), `scripts/agent-sign.sh` (new) | Refuse before start (mode, risk, gate 1, previous gate, artifact, kill switch). Build the prompt from docs/gates.md and the gate's artifacts. Run `${TRIPOD_CLAUDE:-claude} -p --model <m> --output-format json --allowedTools Read,Grep,Glob`. Parse the verdict. On APPROVE: write `event=mode` (first time), then the signature. If activity.log has no usage for the session (plugin hooks not loaded), write one usage record from `modelUsage` marked `source=agent-sign`. | R4–R7, R14, E6 |
| `scripts/activity.py` | `signatures:` line in the summary; signature counts for metrics | R13 |
| `scripts/merge_rules.py` | no logic change expected (auto-merge reads check_change); a test proves R12 | R12 |
| `docs/templates/pod.yml`, `pod.yml` | `mode: pod` and commented autonomous keys (seat models, sponsor) | R1–R3 |
| `scripts/pod_install.py` | copy `docs/autonomous.md` | R17 |
| `tests/test_agent_seats.py` (new) | all requirements and edge cases, using a fake `claude` script | all |
| `docs/autonomous.md` (new), README, AGENTS.md, docs/gates.md, docs/merge-by-risk.md | the mode, seats, sponsor, limits, accepted risk C3 | R17 |
| plugin.json ×2, marketplace.json, tests/test_pod_v3.py version asserts | 0.8.0 (test edit needs PO approval while tests are locked) | release |

## Order of work
1. Write failing tests from the requirements and edge cases in spec.md (a fake `claude` that prints a chosen JSON result), then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. Config keys and `gate-check --all` validation; `make test`
4. `change_mode`, `agent_signature_problem`, check_gate and gate_complete; `make test`
5. `agent_sign.py` and the wrapper, with refusals, the prompt, the verdict and the evidence fallback; `make test`
6. The signatures line in activity.sh and metrics.sh; `make test`
7. Docs, installer, template and version 0.8.0; `make check` and `claude plugin validate --strict` ×3
8. Demo in a copy of tripod-example (`mode: autonomous`, `auto_merge: low`, seats on Sonnet 5.5 and Opus 5.5): a person signs gate 1, then the agents sign gates 2 and 3, review, auto-merge, and gate 4. Run the planted-defect cases 3 times each. Record everything in acceptance.md

## Risks
- A model id rejected by `claude --model`. Reduce: agent-sign checks `modelUsage` and refuses with the model name; the docs list the ids that work.
- The checking agent approves too easily. Reduce: the prompt gives it the gate's questions and asks for a reason per question; R16 measures it with planted defects; low risk only.
- Duplicate cost when the plugin hooks are also loaded globally. Reduce: agent-sign writes usage only when activity.log has none for that session.
- An agent forges signature and evidence lines (C3, accepted). Reduce: the docs tell the sponsor to read the gates.log and activity.log diff in the PR; risk-paths make edits to scripts high.
- Long `claude -p` runs. Reduce: a timeout (`agent_sign_timeout`, default 600 s) and a clear message.

## Proof
- `make test` and `make strength` pass
- R1–R14: unit tests in `tests/test_agent_seats.py` with a fake `claude`, one case per refusal and per gate-check condition
- R15, R16: demo in tripod-example with the real `claude`, recorded in acceptance.md (gates.log, activity.log, verdicts, cost)
- R17: docs reviewed at gate 4

## Rollback
- `git revert <merge commit>` removes agent-sign, the rules and the docs. Then run `make check` and `claude plugin validate --strict`.
- Without a release, any pod can set `mode: pod`: agent-sign refuses, and finished changes keep their recorded mode (C2).

## Summary for SuperBiz
1. Agents get their own seats: once a person approves the intent and says it is low risk, two agents on different models sign the remaining gates for that change, and it can merge on its own.
2. Nothing changes unless a pod turns on `mode: autonomous`; medium and high risk always need people, and the sponsor sees who signed, on which model, and what it cost.
3. Risks: the checking agent could approve too easily, which the demo measures with planted mistakes; and an agent could forge its own evidence, so the sponsor still reads each PR and can stop or revert.
