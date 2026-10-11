## Gate 4 cross, 2026-10-11T04:03:27+00:00

Checking gate 4 as cross (agent:superbiz, claude-sonnet-5-5)...
REFUSE gate 4 cross (agent:superbiz, claude-sonnet-5-5): **Gate 4 cross-check**

**SuperDev**
- **`make check` passes, including test strength: yes, but only as reported.** `review.md:36-37` records 118 tests OK and no weak tests. I can't run commands here, so I didn't re-run it. `review.md:4` pins `reviewed_head: 22a3a51…`, and the commits since then (auto-merge records, acceptance draft, gate 4 sign) are not shown to leave that head's code unchanged.
- **`blockers: 0`: yes.** `review.md:1`.
- **Tests not edited after lock: yes, on the reviewer's word.** `review.md:29` says `tests/` has one commit (a816f50), made before the implementation (103f404), and that `.pod/lock-tests` exists. I didn't check it against git.
- **Signer did not write code (with 2 or more SuperDevs): no, unproven.** The rule needs `review.md` to name the code authors, and it doesn't. No file in the change gives the number of SuperDevs or who wrote the code, so I can't show the signer is separate from the authors.

**SuperBiz**
- **Demo result matches the Success measure: no.** All three measures in `acceptance.md:12-14` pass only by citation. `acceptance.md:8` says "I could not run commands… did not re-run them", and demo steps 2 and 3 say "Not run by hand" (`acceptance.md:22,25`). That is a test report standing in for a demo. The measure in `intent.md:12` is about the behavior of `status_label(code)`, so the demo should have shown it.
- **The name difference is settled by the spec.** `spec.md:18` decides on `support_status_label`, with the risk accepted and a reason given. I'm not refusing on that point.
- **`acceptance.md` states accept or reject with a reason: yes.** `acceptance.md:31-33` gives "accept" with a reason. It is marked "proposed for SuperBiz to confirm", which doesn't block this.

**Risk: high**
- **Escalation signed: not applicable.** `intent.md:18` and `spec.md:19` say Risk is low, and the plan touches no risk paths (`plan.md:40`).

**Other gaps**
- **Success-measure follow-up is open.** The "4 of 40 tickets" figure (`intent.md:6`) has no caller or date yet (`acceptance.md:41`).
- **Extra file in the diff.** `docs/superceo/2026-10-11.md` is not in the plan's "Files to change" (`review.md:25`). It is docs only.

Two items fail or can't be shown: the code authors are not named, and the demo was not run. I'm refusing because I'm unsure about both.

