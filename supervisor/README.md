# supervisor

Owner: Matt. C, core 0 (`0x1`), `SCHED_FIFO` 63. Spawns the other four, heartbeats, restart with backoff, piezo fault path. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1.

## Laptop milestone

In Linux or WSL, run `make -C supervisor test` from the repo root. This builds the supervisor and a dummy worker, kills the worker after its first heartbeat, and checks that a replacement with a different PID sends a heartbeat.

For an interactive run, use `supervisor/build/supervisor supervisor/build/dummy`. The worker sends an `H` byte on stdout every 50 ms. The supervisor logs faults on stderr and restarts the worker on exit or after two missed heartbeats. Ctrl+C shuts down both processes. This harness uses a pipe and a logged piezo stub. QNX pulse delivery, process placement, and GPIO are the next integration step.
