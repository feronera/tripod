# Autonomous mode (low risk)

In Pod mode, every gate is signed by people. In Autonomous mode, a low-risk change needs one person, at gate 1. After that, two agent seats on different models sign gates 2 to 4, and the change merges through the normal auto-merge checks. A **sponsor** watches from outside the loop and can stop or revert any change.

Autonomous mode is off by default. Medium and high risk always need people, in either mode.

## Turning it on

```yaml
mode: autonomous                      # default: pod
superbiz_agent_model: claude-sonnet-5-5
superdev_agent_model: claude-opus-5-5 # must differ from superbiz_agent_model
sponsor_name: Sam
sponsor_email: sam@example.com
sponsor_github: sam-gh
auto_merge: low                       # so a low-risk change can merge without a person
```

`scripts/gate-check.sh --all` (and so CI) fails when a seat model or a sponsor key is missing, or when both seats use the same model. The sponsor may also hold a pod role.

## Who signs what

| Gate | Risk: low in Autonomous mode | Anything else |
|---|---|---|
| 1 (intent) | People: owner and cross. **They decide the change is low.** | People |
| 2 (spec) | `agent:superbiz` owner, `agent:superdev` cross | People |
| 3 (plan) | `agent:superdev` owner, `agent:superbiz` cross | People |
| 4 (acceptance) | Agents, after the auto-merge (post-merge acceptance) | People |

A person's signature always counts, and a gate can mix a person and an agent.

## How an agent signs

```bash
scripts/agent-sign.sh docs/changes/005-x 2   # signs the next open seat: owner, then cross
```

The command does the following:
1. Refuses, before starting any agent, when:
   - the pod is in `mode: pod`;
   - the change is not `Risk: low`;
   - the gate is 1;
   - the gate before is incomplete;
   - the artifact is missing;
   - the gate is already signed;
   - `.pod/kill-switch` exists.
2. Starts `claude -p --model <seat model> --output-format json --allowedTools Read,Grep,Glob` with the gate's questions from `docs/gates.md` and the change's artifacts. The owner seat is told it is accountable for the artifact. The cross seat is told to find what the other leg missed.
3. Reads the verdict from a last line `VERDICT: APPROVE` or `VERDICT: REFUSE`. Anything else counts as REFUSE.
4. Checks that Claude Code's `modelUsage` shows the seat's model actually ran.
5. On APPROVE, appends to gates.log. On the first agent signature it also records the mode and the seat models:
   ```
   event=mode mode=autonomous superbiz_agent_model=claude-sonnet-5-5 superdev_agent_model=claude-opus-5-5 at=…
   gate=2 role=owner by=agent:superbiz model=claude-sonnet-5-5 session=7cc5c1d8-… at=… blob=…
   ```
6. Makes sure activity.log has usage for that session. The plugin hooks write it; if they are not loaded, agent-sign writes one record from Claude Code's own numbers, marked `source=agent-sign`.

Agents run `agent-sign.sh`, never `scripts/gate.sh`, which stays for people and signs as the git email.

`agent_sign_timeout` in pod.yml (seconds, default 600) limits each run.

## What gate-check accepts

An agent signature counts only when all of these hold:
1. The change was signed in Autonomous mode.
2. The change is `Risk: low`.
3. The gate is 2, 3 or 4.
4. `by=agent:<leg>` is the seat that role needs at that gate.
5. `model` is the seat model recorded for the change.
6. activity.log has usage for that `session` and `model`.

Owner and cross must also be on different models. Staleness, signing order, "risk only goes up after gate 1" and risk-paths all apply as for people. A change that touches a path in `docs/risk-paths` is high at merge, so auto-merge refuses it and people take over.

A change keeps the mode and seat models it was signed with. A pod that switches back to `mode: pod` stops new agent signatures, and its finished changes keep passing.

## The sponsor

The sponsor signs nothing. The sponsor is on the loop, not in it:
- reads each PR, including the gates.log and activity.log lines (`scripts/activity.sh` shows `signatures: people 2, agents 6 (…)` and the cost);
- creates `.pod/kill-switch` to stop every agent at once;
- reverts a change and records it with `scripts/mark-revert.sh`, which also stops auto-merge until there is a new track record.

Budgets, a risk ceiling, automatic stops and a daily digest are planned (roadmap step 3).

## Limits you accept

- **Forgery.** An agent that can edit files could write a signature line and a matching usage line by hand. Defenses:
  - the evidence has to match;
  - the low-risk limit and risk-paths (edits to scripts are high);
  - CI, and the sponsor reading the diff;
  - the kill switch and revert.

  There are no cryptographic signatures.
- **Agreeable reviewers.** A checking agent can approve too easily. The prompt makes it answer each gate question with evidence. Measure it on your own work, for example with a planted mistake, before you rely on it.
- **Cost.** Every agent signature is one `claude -p` run. Its cost lands in activity.log.
