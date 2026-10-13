# UX brief: Signed plans stay valid after a kit upgrade

References: intent.md

The users are pod members and CI running `scripts/gate-check.sh` after a kit upgrade. No new screens and no new messages.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/gate-check.sh --all` | Check every change after an upgrade | `OK <change> (passed up to gate N …)` per change, as today | Merge the upgrade |
| `scripts/gate.sh <dir> 3` | Sign a plan | the existing refusal for structure problems | Fix plan.md, then sign |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| gate-check | As today | Not applicable | As today, for unsigned or stale plans only | Finished changes stay `OK` after an upgrade |
| gate.sh 3 | As today | Not applicable | `Refused: plan.md does not follow the required structure, so gate 3 cannot be signed` (unchanged) | As today |

## Copy
| key | Text | Notes |
|---|---|---|
| adopt_upgrade | After the update, run `scripts/gate-check.sh --all`. If it refuses one person in two roles, set `bootstrap: on` ([scaling.md](scaling.md)) or fix pod.yml. | One new line in docs/adopt.md, step 9 |

## Accessibility notes
- No change to output format.
