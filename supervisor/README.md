# supervisor

Owner: Matt. C, core 0 (`0x1`), `SCHED_FIFO` 63. Spawns the other four, heartbeats, restart with backoff, piezo fault path. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1.

## Laptop milestone

In Linux or WSL, run `make -C supervisor test` from the repo root. This builds the supervisor and a dummy worker, kills the worker after its first heartbeat, and checks that a replacement with a different PID sends a heartbeat.

For an interactive run, use `supervisor/build/supervisor supervisor/build/dummy`. The dummy publishes a monotonic heartbeat in the guided block of /beacon_world. The supervisor reads it under seq_guided, faults after two missed 50 ms intervals, and resets its restart delay to 100 ms after ten healthy seconds. It inherits the worker's stdout for logs. For a real laptop run, build guided and pass guided/build/guided --create as the child. Ctrl+C shuts down both processes. The test uses a private shared-memory name. QNX pulse delivery, process placement and GPIO remain integration work.
