# supervisor

Owner: Matt. C, core 0 (`0x1`), `SCHED_FIFO` 63. Spawns the other four, heartbeats, restart with backoff, piezo fault path. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1.

## Laptop milestone

In Linux or WSL, run `make -C supervisor test` from the repo root. This builds the supervisor and a dummy worker, kills the worker after its first heartbeat, and checks that a replacement with a different PID sends a heartbeat.

For an interactive run, use `supervisor/build/supervisor supervisor/build/dummy`. The dummy publishes a monotonic heartbeat in the guided block of /beacon_world. The supervisor reads it under seq_guided, faults after two missed 50 ms intervals, and resets its restart delay to 100 ms after ten healthy seconds. It inherits the worker's stdout for logs. For a real laptop run, build guided and pass guided/build/guided --create as the child. Ctrl+C shuts down both processes. The test uses a private shared-memory name.

## QNX heartbeat integration

Build both programs on the Pi with a QNX compiler, then run these commands from the repository root:

```sh
make -C guided
make -C supervisor
supervisor/build/supervisor guided/build/guided --create
```

For a child named `guided`, the QNX build creates a channel for each launch and appends `--sup PID:CHID` to the child arguments. The supervisor waits for the guided heartbeat pulse with a 50 ms receive timeout and also checks the shared-memory timestamp. Two missed intervals on either path trigger the watchdog. The channel is destroyed after reaping the child so queued pulses cannot clear the replacement's fault.

On the Pi, check for a heartbeat with the new PID, stop that guided child, and verify a fault followed by a heartbeat from its replacement. The fault indicator is currently logged. GPIO output, scheduling verification and the loaded timing trace still need hardware integration.
