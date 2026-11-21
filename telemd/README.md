# telemd

Owner: Matt. Optional sixth process, lowest priority, `0xe`. Read-only on `/beacon_world` and `/beacon_frames`. Sends world-state JSON (~10 Hz) and a downscaled JPEG (~5 fps) over UDP to a laptop on the local network so the team can monitor. Never writes shm, never talks to `guided`. Killing it must not change what the wearer hears. Not a cloud path. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §3 (remote monitor), §6.

JSON format: [`laptop/samples/`](../laptop/samples/).
