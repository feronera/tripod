blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: <git rev-parse HEAD of the reviewed commit>

# Review: <change title>

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.
`second_opinion: agree` means reviewer-second found no Blocker that the main reviewer missed and does not dispute the "no Blocker" result.

## Blocker
- <path:line problem (checklist item / R?) -> what must be fixed, or "none">

## Major
- <path:line problem -> fixed, or why it is not fixed>

## Minor
- <path:line problem>

## Second opinion (reviewer-second)
- <reviewer-second's result and any points of disagreement>

## Checks
- `make check`: <pass or fail>
- `scripts/test-strength.sh`: <pass or fail>
