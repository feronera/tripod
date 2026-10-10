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
   - `.pod/kill-switch` exists;
   - the branch touches a path in `docs/risk-paths` (its effective risk is high);
   - the branch, committed or not, edits agent instructions or gate rules (`CLAUDE.md`, `AGENTS.md`, `.claude/`, `.mcp.json`, `docs/gates.md`, `docs/risk-paths`, `docs/model-prices`), which could steer its own checker or its own budget. Auto-merge refuses these files too, in either mode;
   - it is gate 4 and there is no auto-merge record yet.
2. Starts `claude -p --model <seat model> --output-format json --tools Read,Grep,Glob --safe-mode --strict-mcp-config`. Only these tools exist in that session, whatever the user's settings allow; the repository's CLAUDE.md, hooks, plugins and MCP servers are not loaded with the gate's questions from `docs/gates.md` and the change's artifacts. The owner seat is told it is accountable for the artifact. The cross seat is told to find what the other leg missed.
3. Reads the verdict from the last line, `VERDICT: APPROVE` or `VERDICT: REFUSE`. It approves only when that is the one and only VERDICT line, so text quoted from an artifact cannot decide it. Anything else counts as REFUSE.
4. Checks that Claude Code's `modelUsage` shows the seat's model actually ran.
5. On APPROVE, appends to gates.log. On the first agent signature it also records the mode and the seat models:
   ```
   event=mode mode=autonomous superbiz_agent_model=claude-sonnet-5-5 superdev_agent_model=claude-opus-5-5 at=…
   gate=2 role=owner by=agent:superbiz model=claude-sonnet-5-5 session=7cc5c1d8-… at=… blob=…
   ```
6. Records the run in activity.log for every run, approved or refused: one usage record per model from Claude Code's own numbers (`source=agent-sign`), and an `event=verdict` record. A run that times out or fails before returning JSON has no numbers to record.

Agents run `agent-sign.sh`, never `scripts/gate.sh`, which stays for people and signs as the git email.

`agent_sign_timeout` in pod.yml (seconds, default 600) limits each run.

## What gate-check accepts

An agent signature counts only when all of these hold:
1. The change was signed in Autonomous mode.
2. The change is `Risk: low`.
3. The gate is 2, 3 or 4.
4. `by=agent:<leg>` is the seat that role needs at that gate, and the line has a `session` and a `model`.
5. `model` is the seat's model in pod.yml (for a finished change in a pod that switched back, the model recorded with it on the base branch).
6. activity.log has usage for that `session` and `model`.
7. That session backs no other signature, and its run did not end in REFUSE.
8. At gate 4, gates.log has an auto-merge record.

Owner and cross must also be on different models. Model ids must match exactly: `claude-opus-5-5` in pod.yml does not match a dated or `[1m]` variant.

In either mode, pod.yml may not give a person an email or GitHub login starting with `agent:`, and `mode` must be `pod` or `autonomous`. Staleness, signing order, "risk only goes up after gate 1" and risk-paths all apply as for people. A change that touches a path in `docs/risk-paths` is high at merge, so auto-merge refuses it and people take over.

In `mode: pod`, agent signatures count only for a finished change: one whose `event=mode` record is already on the base branch. A record written on a branch never turns Autonomous mode on by itself. So a pod that switches back stops new agent signatures, and its merged changes keep passing.

## The sponsor

The sponsor signs nothing. The sponsor is on the loop, not in it:
- reads each PR, including the gates.log and activity.log lines (`scripts/activity.sh` shows `signatures: people 2, agents 6 (…)` and the cost);
- creates `.pod/kill-switch` to stop every agent at once;
- reverts a change and records it with `scripts/mark-revert.sh`, which also stops auto-merge until there is a new track record.

### Limits and automatic stops

The sponsor sets limits in pod.yml. Each is optional; a missing key means no limit. They apply only to agent work (`agent-sign.sh` and auto-merge), never to people's commands.

| Key | What happens |
|---|---|
| `budget_per_change_usd` | agent-sign refuses when the change's spend plus the next run would pass it |
| `budget_per_day_usd` | the same, over the last 24 hours, for the whole pod |
| `max_refusals_per_gate` | after this many refused agent checks on a gate, agent-sign refuses until a person signs a gate of the change or runs `scripts/resume.sh <dir> "<reason>"` |
| `agent_merges_per_day` | auto-merge refuses once this many changes were auto-merged in the last 24 hours |
| `agent_forbidden_paths` | agent-sign and auto-merge refuse a change that touches these globs; people can still change them at Risk: low |

Agents also pause for 24 hours after any revert.

Spend comes from activity.log, read from the working tree and from the base branch, so a revert or an auto-merge already on main counts on every branch (other unmerged branches are not seen). A cost that is not a finite amount of 0 or more counts as unknown. A record with no readable time still counts toward its change, but not toward any time window. Resumes and people's signatures count only from the sponsor or a member. `TRIPOD_NOW`, used by tests, can only move the clock back, which makes limits stricter. The next run is estimated from the most expensive agent-sign run of the last 7 days. A running session is never cut off, so a day can end slightly over budget; the digest shows it. When a budget is reached, the activity hook tells the agent in its session, once per session per limit.

`scripts/resume.sh` is for people: it records `event=resume` in gates.log with the git email, which must be the sponsor's or a member's. Agents never run it.

### The daily digest

```bash
scripts/digest.sh              # the last 24 hours
scripts/digest.sh --hours 72   # a longer window
scripts/digest.sh --write      # also save docs/digest/YYYY-MM-DD.md (UTC date)
```

It lists spend (total, per change, per model, unknown), agent signatures, refused checks, auto-merges, reverts, resumes, stops in force and the limits, from the same records the stops use. Sending it to Slack, email or an issue is left to the team, for example with a scheduled CI job.

## Limits you accept

- **Forgery.** An agent that can edit files could write a signature line and a matching usage line by hand. Defenses:
  - the evidence has to match;
  - the low-risk limit and risk-paths (edits to scripts are high);
  - CI, and the sponsor reading the diff;
  - the kill switch and revert.

  There are no cryptographic signatures. The same holds for `TRIPOD_CLAUDE`, which tests use to replace `claude`: whoever can set it can also edit the files.
- **Agreeable reviewers.** A checking agent can approve too easily. The prompt makes it answer each gate question with evidence. Measure it on your own work, for example with a planted mistake, before you rely on it.
- **Cost.** Every agent signature is one `claude -p` run. Its cost lands in activity.log.
- **Limits are checked before a run, not during it.**
  - Several agent-sign runs started at the same moment all pass the same check, so spend can overshoot by one estimate per run.
  - Branches that are not merged do not see each other's spend or merges.
  - A run that fails before it returns a verdict is not counted as a refusal.
  - The budget warning also reaches a person's own Claude Code session in the repository, because the hook cannot tell people from agents.
  - The digest shows all of this the next day.
