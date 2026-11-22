# Working notes (not shipped)

Untracked by design. The product and geometry source of truth is
`docs/nathans-revision.md`; this directory is the implementation paper trail.

## Where things are

- `sdd/progress.md` — living ledger of what landed, what is gated, what is open.
- `sdd/archive/` — per-task briefs, implementation reports and reviews.
- `<repo>/docs/superpowers/plans/` — the world-frame dots plan (tracked).

## Review verdicts

Every bounded step got an independent reviewer pass. Latest verdict per task:

| Task | Verdict | Detail |
|---|---|---|
| `2` | BLOCK | `archive/task-2-review.md` |
| `3` | OK with notes | `archive/task-3-review.md` |
| `4` | BLOCK on original `00eb6c3`; follow-up commit applies P1/P2. | `archive/task-4-review.md` |
| `4-followup` | OK with notes | `archive/task-4-followup-review.md` |
| `5` | OK with notes | `archive/task-5-review.md` |
| `cadence` | OK with notes | `archive/task-cadence-review.md` |
| `depth-polish` | OK with notes | `archive/task-depth-polish-review.md` |
| `depth-slots` | OK with notes | `archive/task-depth-slots-review.md` |
| `depth-stability` | OK with notes | `archive/task-depth-stability-review.md` |
| `dev-reach-hold-hand-p2` | OK | `archive/task-dev-reach-hold-hand-p2-review.md` |
| `dev-reach-hold-lost` | OK with notes | `archive/task-dev-reach-hold-lost-review.md` |
| `fov` | OK with notes | `archive/task-fov-review.md` |
| `fov-p2` | OK | `archive/task-fov-p2-review.md` |
| `hold-lost` | OK with notes | `archive/task-hold-lost-review.md` |
| `hold-lost-p2` | OK | `archive/task-hold-lost-p2-review.md` |
| `hold-objects` | OK with notes | `archive/task-hold-objects-review.md` |
| `hold-objects-p2` | OK | `archive/task-hold-objects-p2-review.md` |
| `jpeg-corrective` | OK with notes | `archive/task-jpeg-corrective-review.md` |
| `jpeg-video` | BLOCK | `archive/task-jpeg-video-review.md` |
| `range-readout` | OK with notes | `archive/task-range-readout-review.md` |
| `range-readout-p2` | OK | `archive/task-range-readout-p2-review.md` |
| `sha-table` | OK | `archive/task-sha-table-review.md` |
| `spec-labels-makefile` | OK with notes | `archive/task-spec-labels-makefile-review.md` |
| `tape-check` | OK with notes | `archive/task-tape-check-review.md` |
| `tape-check-p2` | OK | `archive/task-tape-check-p2-review.md` |
| `target-names` | OK | `archive/task-target-names-review.md` |
| `vocab-expansion` | OK with notes | `archive/task-vocab-expansion-review.md` |
| `yolo-runtime-fixup` | OK | `archive/task-yolo-runtime-fixup-review.md` |
| `yoloe-32` | OK with notes | `archive/task-yoloe-32-review.md` |

Two BLOCKs were raised and both were corrected, not waived: the calib `--camera`
burst capture (`00eb6c3`), and the JPEG `--jpeg` no-op flag plus cycle timing
(`5f4f1db`, `c54220e` -> `7c1af8b`).

## Regenerating a review diff

Diffs are deleted to keep this light; they are derivable from git:

```sh
git show <sha>                 # one commit
git diff <from>..<to>          # a range
```
