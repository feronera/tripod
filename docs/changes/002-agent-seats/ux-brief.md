# UX brief: Agent seats and agent signatures

References: intent.md

The users are the sponsor (reads evidence after the fact), pod members (still sign gate 1, and any gate in Pod mode) and the agents themselves (run `agent-sign.sh`). Everything is plain text in a terminal, CI logs and the PR.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/agent-sign.sh <dir> <gate>` | An agent signs one seat of a gate on its configured model | seat, model, verdict, reasons, the gates.log line written | Sign or refuse |
| `scripts/gate-check.sh <dir>` | Check gates, now including agent signatures | per gate: who signed (person or agent:leg/model), problems | Fix or sign |
| `scripts/activity.sh <dir>` (new line) | Show the sponsor who signed what | `signatures: people 2, agents 6 (claude-opus-5-5 3, claude-sonnet-5-5 3)` | Read |
| `scripts/metrics.sh <dir>` (new line) | Compare changes | `signatures: people 2, agents 6` | Compare |
| `gate-check --all` (pod.yml) | Catch a bad Autonomous setup | missing sponsor or seats, same model twice | Fix pod.yml |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| agent-sign | Not applicable (needs a change and a gate) | `Checking gate 2 as owner (agent:superbiz, claude-sonnet-5-5)...` while the agent runs | Refused before start: `Refused: <reason>` (pod mode, not low, gate 1, gate before incomplete, missing artifact, kill switch). Agent refused: `REFUSE gate 2 owner (agent:superbiz, claude-sonnet-5-5)` and the reasons, exit 1. Agent failed: `agent-sign: claude did not return a verdict (<reason>). Nothing was recorded`, exit 1 | `APPROVE gate 2 owner (agent:superbiz, claude-sonnet-5-5)`, the recorded line, and what is still missing for the gate |
| gate-check | `OK: no changes in docs/changes/ yet` (unchanged) | Not applicable | Per condition, for example `gate 2: agent signature by agent:superbiz has no usage for session 7cc5… with claude-sonnet-5-5 in activity.log` | `OK   002-x (passed up to gate 3, Risk: low, agents signed 4)` |
| activity.sh / metrics.sh | `signatures: none yet` | Not applicable | Not applicable | `signatures: people 2, agents 6 (…)` |

## Copy
| key | Text | Notes |
|---|---|---|
| refuse_mode | Refused: pod.yml sets mode: pod. Agents may sign only in mode: autonomous | agent-sign |
| refuse_risk | Refused: Risk is {risk}. Agents may sign only Risk: low changes; medium and high need people | agent-sign |
| refuse_gate1 | Refused: gate 1 is always signed by people, who decide the risk | agent-sign |
| refuse_kill | Refused: kill switch is on (.pod/kill-switch). No agent was started | agent-sign |
| checking | Checking gate {n} as {role} ({by}, {model})... | agent-sign, while running |
| approve | APPROVE gate {n} {role} ({by}, {model}) | agent-sign |
| refuse | REFUSE gate {n} {role} ({by}, {model}): {reasons} | agent-sign |
| no_verdict | agent-sign: claude did not return a verdict ({reason}). Nothing was recorded | agent-sign |
| no_evidence | gate {n}: agent signature by {by} has no usage for session {session} with {model} in activity.log | gate-check |
| wrong_model | gate {n}: agent signature by {by} used {model}, but pod.yml sets {leg}_agent_model: {expected} | gate-check |
| same_model | gate {n}: owner and cross were both signed by {model}; the cross-check must run on a different model | gate-check |
| not_allowed | gate {n}: agent signature not allowed here ({reason}: pod mode, Risk not low, or gate 1) | gate-check |
| config_missing | pod.yml: mode: autonomous needs {key} | gate-check --all |
| signatures | signatures: people {p}, agents {a} ({by model}) | activity.sh, metrics.sh |

## Accessibility notes
- Plain text; the words APPROVE and REFUSE carry the meaning, not color.
- Session ids are shortened to 8 characters in messages, full in gates.log.
- Every refusal says what to do next or who must act (a person, or fix pod.yml).
