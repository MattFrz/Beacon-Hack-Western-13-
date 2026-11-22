# ingest

The missing wire: percept probe world records in, `/beacon_world` out.

Owner: Nathan (plan step 4, `docs/qnx-integration-plan.md`).

```
probe_to_world.py --udp 127.0.0.1:5006  ->  ingest  ->  /beacon_world (seq_percept)
                                                    guided reads it at 60 Hz
```

The probe emits one world-record JSON object per UDP datagram (the same
schema as `--out` JSONL). `guided` reads `/beacon_world`. Nothing connected
the two; this process does, on the device itself. It is the stand-in for the
native C++ `percept` writer until that lands, and it stays useful after: it is
also how a recorded `.jsonl` replay drives the real `guided` on the Pi.

## What it writes (and never writes)

- **Only `seq_percept`**: `pose`, `objects[]`, `hand`, `health`. Timestamps
  pass through as capture times; `hb_percept_ns` is refresh time.
- **Never** `seq_guided` (guided owns the target bind), never `crumbs`
  (preserved from the block already in shm, per the spec §5 restart-attach
  rule; `RETURN` is cut from Sunday anyway).
- `health.p95_vision_ns` is preserved across records — it is a measurement.
- Malformed datagrams (a JPEG preview aimed here by mistake, torn JSON) are
  counted and dropped. Newest record wins; there is no queue.

## Usage

```
ingest [--create] [--udp [PORT]] [--stdin] [--intent KIND[:name,...]] [--verbose]
```

- `--udp` listens on PORT (default **5006**; the laptop bridge owns 5005).
  On the Pi: `probe_to_world.py --udp 127.0.0.1:5006 --jpeg ...` with the
  JPEG aimed at the bridge, not here.
- `--stdin` reads one record per line (replay a `.jsonl`).
- `--intent FIND:keys,keychain` is a **bring-up stand-in for `voiced`**: it
  writes one intent under `seq_voiced` AFTER the first record lands (an
  earlier intent would find no objects and guided would NACK
  "I have not seen that"). Kinds: NONE FIND GO RETURN STOP REPEAT REJECT
  NACK_UNHEARD NACK_UNSEEN NACK_CANT. When real `voiced` runs, drop the flag.
- `BEACON_WORLD=/beacon_x` overrides the shm name (same escape hatch as
  supervisor's `BEACON_SUPERVISOR_WORLD`). Tests use it; the product path
  never sets it.

On QNX: `SCHED_RR` 22 with runmask `0xe` (cores 1–3, never core 0). Laptop:
same binary, prints that the scheduler call was skipped.

## Build / test

- `make` (laptop `cc`, or `make CC="qcc -Vgcc_ntoaarch64le"` cross, or plain
  `make` on the Pi).
- `make test` runs `tests/test_ingest.py`: an end-to-end sweep that feeds
  probe-schema records over UDP and asserts `guided` says a WALK cue
  ("keys ahead"), enters REACH (ticks, then a tone), and then — after the
  records stop — says "I lost the target". That is the Sunday sequence minus
  real vision, in ~15 s, no camera, no model.

## Known limits (deliberate)

- The JSON parser (`src/json.c`) is a small bounded arena parser for the
  probe's record shape only. It is not a general JSON library; do not reuse
  it outside ingest without reading its header comment.
- `d_m` in the record is ignored: guided computes reach distance itself from
  `hand`/`target` geometry (spec §7 Range 1), so the relay must not smuggle
  in a second distance author.
