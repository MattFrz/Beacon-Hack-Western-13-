# supervisor

Owner: Matt. C, core 0 (`0x1`), `SCHED_FIFO` 63. Spawns the stack, watches heartbeats, restarts with backoff. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1. Judging notes: [`docs/qnx-prize-track.md`](../docs/qnx-prize-track.md).

Two modes.

## `--beacon`: the stack, as the spec's process table

```sh
# on the loaner, after the sensor service is up (it needs root itself)
cd /data/home/qnxuser/Beacon-Hack-Western-13-
sudo ./supervisor/build/supervisor --beacon --metres
```

What it does, in order: creates `/beacon_frames`, `/beacon_depth` and `/beacon_world` (zeroed only when new, so a supervisor restart does not wipe a session), stamps the world with the ABI, then spawns:

| Child | Policy / prio | Runmask | Heartbeat | On death |
| --- | --- | --- | --- | --- |
| `guided` | `SCHED_FIFO` 58 | `0x1` | `hb_guided_ns` (seq_guided) | **fault**: kill, log, respawn |
| `ingest` | `SCHED_RR` 20 | `0x2` (CPU 1) | none, liveness only | restart with backoff |

Spawn uses `POSIX_SPAWN_SETSCHEDULER` / `POSIX_SPAWN_SETSCHEDPARAM` with the priority from `include/beacon.h`. `POSIX_SPAWN_SETRUNMASK` does not exist in this SDP, so the runmask comes from the child's own `ThreadCtl` on every thread it creates (`guided` does this in `platform_set_thread_sched`; `ingest` in `apply_sched`). The table's mask is what the child is expected to apply. Every child also sets its own runmask on every thread it creates (`guided` does this in `platform_set_thread_sched`). On QNX the supervisor owns a 50 ms `CLOCK_MONOTONIC` pulse timer over `ChannelCreate`; a child that pulses (`guided --sup <pid>:<chid>`, which is passed automatically) refreshes the beat early.

Options:

| Flag | Meaning |
| --- | --- |
| `--metres` | pass `--metres` to guided (only after the tape check) |
| `--guided-args "..."` | extra argv for guided, e.g. `"--duration 120"` |
| `--ingest-args "..."` | extra argv for ingest, e.g. `"--udp 5006"` |
| `--with "CMD ..."` | extra supervised child at `SCHED_RR` 20 on `0xe` (repeatable) |
| `--dry-run` | print the spawn table and exit |
| `--create` | create the regions without spawning (both modes) |

Paths come from `BEACON_GUIDED` and `BEACON_INGEST` if set, otherwise `guided/build/guided` and `ingest/build/ingest` relative to the current directory.

If the kernel refuses the scheduler attributes (a laptop, or no `PROCMGR_AID_PRIORITY`), the spawn is retried without them and the log says so. The stack comes up either way; only the placement claim is lost.

## `CHILD [ARG ...]`: one child, laptop shape

```sh
make -C supervisor test          # kill, stale heartbeat, backoff reset
./build/supervisor ./build/dummy
./build/supervisor ./guided/build/guided --create --duration 10
```

No scheduler attributes are requested here, so this runs as an ordinary user. `BEACON_SUPERVISOR_WORLD` points it at a private shm name.

## Tests

| Command | What it proves |
| --- | --- |
| `make test` | single-child restart: `SIGKILL`, `SIGSTOP` (stale beat), backoff reset after ten healthy seconds, stdout cannot clear a fault |
| `make test-beacon` | the real stack: guided heartbeats, killing guided faults and respawns while ingest is untouched, `SIGSTOP` on guided is caught by the heartbeat, `SIGTERM` shuts down and exits 0 |

Both run on a laptop. Neither is a QNX scheduler test: the scheduler attributes are only real on the device, and `make test-beacon` prints a note when the kernel refused them.

## Honest limits, 2026-11-21

- **No second output channel.** There is no buzzer, transistor or LED on hand, so a guided fault is a log line and a fast respawn, not a fault tone. The pitch must not claim one. If `guided` dies the wearer hears nothing until the respawn lands.
- **`camd` publishes no heartbeat.** Only liveness. `telemd` and the laptop dashboard are never supervised.
- **The heartbeat source is the seqlocked shm field**, because that is what every writer already publishes. Pulses carry the supervisor's own tick and refresh the beat when a child sends one; a failed pulse attach cannot kill-loop guided.
- **Multi-bit runmasks are rejected by this image.** Measured 2026-11-21 as root: `0x3`, `0x6`, `0x7`, `0xc`, `0xe` all return `EINVAL`; `0x1`, `0x2`, `0x4`, `0x8`, `0xf` succeed, through both `ThreadCtl` forms. That is why `ingest` pins one core off core 0 instead of cores 1-3, and why it logs the kernel's readback. `pidin -F %i` renders empty here, so the process's own readback is the evidence.

Verified on the loaner 2026-11-21: builds with the device `cc`, spawns both children, `pidin` shows `58f` / `40f` for guided and `22r` for ingest with `last_cpu=0` and `last_cpu=1`, `kill -9 guided` produces `guided fault (no output channel)` and a respawn, 300 loops with 0 missed deadlines while that ran.
