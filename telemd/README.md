# telemd

Owner: Matt. Optional sixth process, lowest priority, `0xe`. Read-only on `/beacon_world` and `/beacon_frames`. Sends world-state JSON (~10 Hz) and a downscaled JPEG (~5 fps) over UDP to a laptop on the local network so the team can monitor. Never writes shm, never talks to `guided`. Killing it must not change what the wearer hears. Not a cloud path. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §3 (remote monitor), §6.

JSON format: [`laptop/samples/`](../laptop/samples/).

## Live target telemetry

From the repository root on Linux or WSL, run `make -C telemd`, then `telemd/build/telemd`. The default destination is `127.0.0.1:5005`. To use a bridge on another host, pass its IPv4 address and optional UDP port. With WSL NAT and a Windows-hosted bridge, use the Windows host address reachable from WSL.

The sender waits for the shared world, opens it read-only, and sends a version-1 JSON datagram about every 100 ms. Each message includes the monotonic timestamp, guided and percept sequence numbers, mode, law, and bound target (or null). Reads that overlap a write are retried or skipped.

To exercise it with the laptop simulator, run the bridge in live mode, start the sender, then run `bash guided/tools/run_scenario.sh reject` from the repo root. A WebSocket client on the bridge should see the target change from keys to keychain. This milestone covers target telemetry. Frame streaming, full-world telemetry and Pi scheduling are pending.
