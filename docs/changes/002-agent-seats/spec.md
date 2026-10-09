# Spec: Agent seats and agent signatures (Autonomous mode for low risk)

References: intent.md, ux-brief.md

## Requirements

Configuration
- R1: The system must read `mode: pod | autonomous` from pod.yml, default `pod`. In `pod` mode every existing behavior is unchanged and agent signatures are never accepted. (verified by: test; all existing tests keep passing)
- R2: The system must read the agent seats from pod.yml: `superbiz_agent_model` and `superdev_agent_model` (a model id, for example `claude-sonnet-5-5`, `claude-opus-5-5`). `gate-check --all` must fail in `autonomous` mode when either is missing or when both are the same model. (verified by: test)
- R3: The system must read the sponsor from pod.yml: `sponsor_name`, `sponsor_email`, `sponsor_github`. `gate-check --all` must fail in `autonomous` mode when the sponsor is missing. The sponsor may also hold a pod role. (verified by: test)

Signing
- R4: `scripts/agent-sign.sh <change-dir> <gate>` must run the check for one seat as an agent: it starts `claude -p` with the model of the seat that the gate needs next (owner first, then cross), gives it the gate's questions from docs/gates.md and the artifacts, and reads back a verdict `APPROVE` or `REFUSE` with reasons. (verified by: test with a fake `claude` on PATH; demo with the real one)
- R5: On `APPROVE`, the command must append to gates.log: `gate=<n> role=owner|cross by=agent:superbiz|agent:superdev model=<model> session=<session id> at=<time> blob=<artifact hash>`. On `REFUSE` it writes nothing, prints the reasons and exits 1. (verified by: test)
- R6: The command must refuse, before starting any agent, when: the pod is in `pod` mode; the change is not `Risk: low`; the gate is 1; the gate before is not complete; or the artifact is missing. The message names the reason. (verified by: test)
- R7: The model recorded in a signature is the one the command started, and it must equal the seat's model in pod.yml. The command never takes a model or a session id from the agent being checked. (verified by: test)

Checking
- R8: gate-check must accept an agent signature only when all of these hold: `mode: autonomous`; `Risk: low`; gate 2, 3 or 4; `by=agent:<leg>` matches the seat the role needs at that gate (owner and cross legs as for people); `model` equals that leg's model in pod.yml; and activity.log has a usage record with that `session` and `model`. Otherwise the signature is reported as a problem that names the failed condition. (verified by: test, one case per condition)
- R9: For a gate signed by two agents, the owner and cross models must differ. A person's signature still counts for any role, and a gate may mix a person and an agent. (verified by: test)
- R10: Gate 1 must always be signed by people (owner and cross), in both modes. (verified by: test)
- R11: The existing rules keep working with agent signatures: order (owner before cross), staleness by blob hash, risk can only go up after gate 1, and docs/risk-paths make a change high at merge (so `pr-check` and `auto-merge-check` need people again). (verified by: test)
- R12: `auto-merge-check` must accept gates 1 to 3 signed this way, so a low-risk change can merge with no person after gate 1 when `auto_merge: low` and the existing 9 checks pass. Gate 4 owner and cross may then be signed by agents after the merge (post-merge acceptance), and `release-check` accepts them. (verified by: test)

Sponsor and visibility
- R13: `scripts/activity.sh` and the PR summary must show which gates were signed by agents, with the model. `metrics.sh` must count signatures by people and by agents per change. (verified by: test)
- R14: The kill switch (`.pod/kill-switch`) must stop `agent-sign.sh` before it starts an agent. (verified by: test)

Demo and docs
- R15: One low-risk demo change in tripod-example must run in `autonomous` mode from gate 2 to merge with no person signing after gate 1. (verified by: demo, recorded in acceptance.md with gates.log and activity.log)
- R16: A planted defect must be refused by the cross-checking agent in 3 of 3 runs each: a spec that leaves out a requirement in intent.md, and a plan that leaves out a requirement in spec.md. (verified by: demo, recorded in acceptance.md)
- R17: README ("Two modes" and the roadmap), AGENTS.md (agents may run `agent-sign.sh` only in Autonomous mode, never `gate.sh`), docs/gates.md, docs/merge-by-risk.md and a new section in docs/scaling.md (or a new docs/autonomous.md) must describe the mode, the sponsor and the limits. (verified by: review)

## Edge cases
- E1: Empty or missing: no pod.yml sponsor or seat models in autonomous mode: gate-check fails with the missing key (R2, R3). No activity.log or no usage for the session: the signature is refused by gate-check (R8).
- E2: Malformed: a gates.log agent line without `model` or `session`, or with an unknown leg (`by=agent:foo`): reported as a problem, never accepted.
- E3: Permissions: an agent signature at Risk: medium or high, at gate 1, or in pod mode: refused by agent-sign and rejected by gate-check (R6, R8, R10). An agent cannot sign as a person: `gate.sh` still uses the git email, and AGENTS.md forbids agents from running it.
- E4: Risk raised after agent signatures (intent.md edited after gate 1): gate 1 goes stale, so every later gate fails as today.
- E5: The artifact changes after an agent signed: the agent signature goes stale by blob hash, like a person's.
- E6: `claude` is not installed or fails, or the verdict cannot be parsed: agent-sign writes nothing, exits 1 and says why. A verdict that is neither APPROVE nor REFUSE counts as REFUSE.
- E7: The same model configured for both seats: refused by gate-check --all (R2), and agent-sign refuses to run.
- E8: The agent edits gates.log or activity.log by hand to forge a signature: R8 needs matching usage evidence; a forged pair of lines is still possible, so the docs say the sponsor reviews the PR diff, and the limit stays low risk only. Documented as an accepted risk.
- E9: Switching back to `mode: pod` with agent signatures in finished changes: handled as proposed in C2, so finished changes keep passing and no new agent signature is accepted.

## Flagged concerns
- C1 (SuperDev, feasibility, checked 2026-10-09): `claude -p --plugin-dir <superdev plugin> --output-format json` returns `session_id`, and the 0.7.0 hooks write usage for that session to the change's activity.log (seen in the change 001 R10 demo). So agent-sign starts the checking agent with the plugin loaded, on the change branch. Choosing the model with `--model` is to be confirmed in the plan.
- C2 (SuperBiz): what happens to old agent signatures when a pod switches back to `mode: pod`? Proposal: a change keeps the mode it was signed in, recorded once in gates.log (`event=mode mode=autonomous` at gate 2), so turning the mode off stops new agent signatures without failing finished changes.
- C3 (escalation, accepted risk): agent signatures are lines in a file that the agent's own session can edit (E8). The defense is evidence that must match (activity.log), the low-risk limit, risk-paths, CI, the PR diff, the kill switch and revert. Cryptographic signing is out of scope.
- C4: cost. Each agent signature is a `claude -p` run. The cost lands in activity.log (0.7.0), so the sponsor sees it; budgets are change 003.
- C5: this change touches `scripts/**`, so it is Risk: high at merge (matches intent.md). It is merged by people.

## Out of scope
- Medium and high risk in Autonomous mode.
- Budgets, the risk ceiling, automatic stops and the daily digest (change 003).
- The loop driver and the superceo agent (change 004).
- Cryptographic signatures or a separate identity service.
- Agent approvals on GitHub PRs (`pr-check` keeps reading human approvals; low-risk merges use the existing auto-merge record).
- Turning on Autonomous mode for Tripod's own repository.
