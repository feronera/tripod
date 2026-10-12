# UX brief: See changes on other branches

References: intent.md

The user is a pod member running `scripts/new-change.sh` in a terminal.

## Screens
| Screen | Purpose | Data shown | Main action |
|---|---|---|---|
| `scripts/new-change.sh <slug>` | Start a change with a number nobody else holds, within the WIP limit | the new folder, or the refusal with each open change and where it is | Start drafting the intent, or close or delete an open change |

## States
| Screen | empty | loading | error | success |
|---|---|---|---|---|
| new-change.sh | No changes anywhere: `docs/changes/001-<slug>` | Not applicable (local git only) | WIP refusal (copy below); usage error as today | `docs/changes/NNN-<slug>` (unchanged) |

## Copy
| key | Text | Notes |
|---|---|---|
| refused | Refused: {n} open changes reach the WIP limit ({limit}). Take a change through gate 4 first: | First line, unchanged from today |
| open_line | `  - {NNN-slug} ({where})` | where is `working tree`, `branch change/NNN-slug` or `branch origin/change/NNN-slug` |
| stale_hint | Remote branches are as of the last git fetch. | Only when a listed change came from a remote branch |
| abandoned_hint | An abandoned change still counts: delete its branch (git branch -d, git push origin --delete) to free the slot. | Always, as the last line |

## Accessibility notes
- Plain text, one change per line. No color.
- The refusal goes to stderr with exit code 1, as today.
