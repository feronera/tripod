blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: 53e54f2ca9de24fe932f406b5af11d78c812ea5f

# Review: Fixes from the lab rehearsal

## Checks against the spec
| Req | Result |
|---|---|
| R1 next step | After every recorded signature, `gate.sh` prints `Next: share the signature: git add <dir>/gates.log && git commit -m "gate N" && git push`. It is never printed on a refusal |
| R2 repeat refused | Refused when the person's latest entry for the same gate and role has the current blob. Signing after a stale signature is allowed. Bootstrap's owner and escalation step is unaffected |
| R3 `__pycache__/` | Added once to the installer's `.gitignore` lines |
| R4 existing tests | Unchanged, except the two installer assertions listing the exact `.gitignore` lines. Each gains `__pycache__/`, with the PO's approval (the spec was amended and gates 2 and 3 signed again) |

## Rehearsal (the success measure)
The pod deck's Labs 0 to 9 were run with this branch's kit, without the stand-in steps:
- every signature printed the next step;
- the kit's `.gitignore` had `__pycache__/`, and Lab 7's auto-merge-check gave only its two expected reasons (no "210 lines");
- Lab 3 produced all six refusals, including the new repeat-signature one;
- Lab 9 showed agent cost;
- `make check` passed at the end.

## Second opinion (Sonnet 5.5, independent)
- blockers_found 0, verdict agree.
- The 3 new behavior tests fail on main; the 3 guard tests pass on both.
- No wrong refusal was found: letter case, several people in a role, bootstrap, role=auto, stale signatures and old logs were all checked.

| Finding | Severity | Outcome |
|---|---|---|
| If bootstrap is turned on after the owner signed alone, the owner cannot re-sign to add escalation | Low | Accepted: rare; the escalation person signs directly |
| A path with spaces is not quoted in the Next line | Low | Accepted: change folders use `NNN-slug`, which has no spaces |
| `__pycache__` without a slash, or `*.pyc`, is not detected, so a harmless duplicate line is added | Low | Accepted |

## Checks
- `make check`: pass (418 tests)

## Gates
On 2026-10-13 the PO asked the agent to run every signature for this change ("Yes, do it all").

## Code authors
64177747+hx-natthawat@users.noreply.github.com (one SuperDev in the pod, so peer review does not apply)
