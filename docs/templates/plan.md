# Plan: <change title>

References: intent.md, spec.md

## Data shape
<the core data and the structure that organizes it, e.g. a table, state machine or typed record, before any logic is written>

## Throughput checkpoint
- Blocking first steps: <work that must finish before anything else can start>
- Independent workstreams: <work that can proceed separately, or n/a: <reason>>
- Shared mutable state: <files or data that several parts must edit, or n/a: <reason>>
- Smallest safe decomposition: <the smallest split in which each part ends with a check>

## Parallel parts
<optional. If the work is not split, write `none: <reason>`>
### A
files: app/a.py, app/b.py
### B
files: app/c.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| <path> | | R1 |

## Order of work
1. Write failing tests from the edge cases in spec.md, then commit
2. Lock the tests (`touch .pod/lock-tests`)
3. <next unit: the smallest change that ends with `make test` passing>

## Risks
- <technical risk and how to reduce it>

## Proof
- `make test` and `make strength` pass
- <how each requirement is proven>

## Rollback
- <how to roll back, e.g. git revert <commit>, and what to check afterwards>

## Summary for SuperBiz
1. <what is being done>
2. <how it affects users>
3. <risks SuperBiz should know about>
