# UX brief: One trusted base branch

References: intent.md

The users are pod members, agents and CI running the kit's scripts. Plain text in a terminal and CI logs.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/gate-check.sh --all` | Check the pod and every change | the base problem as a pod.yml problem | Fix `base_branch` in pod.yml |
| `scripts/agent-sign.sh` | An agent signs | the existing "pod.yml has problems" refusal, listing the base problem | A person fixes pod.yml |
| `scripts/gate.sh <dir> 4` | Gate 4 owner signature with 2+ SuperDevs | refusal with the base problem | Fix pod.yml, then sign |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| gate-check --all | As today | Not applicable | `FAIL pod.yml` with the base problem | As today |
| gate.sh 4 | As today | Not applicable | `Refused: peer review cannot be checked: <base problem>` | As today |

## Copy
| key | Text | Notes |
|---|---|---|
| change_base | base_branch: {name} is a change branch; the base must be the shared branch changes merge into (pod.yml base_branch, default main) | Same text as the loop today |
| ci_mismatch | base_branch: {name} does not match the pull request's base branch {ci} | CI only |
| peer_refused | Refused: peer review cannot be checked: {problem} | gate.sh, gate 4 owner, 2+ SuperDevs |

## Accessibility notes
- Plain text, one problem per line.
