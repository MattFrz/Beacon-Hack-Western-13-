# telemd

Owner: Matt. Optional sixth process, lowest priority, `0xe`. Read-only on `/beacon_world` and `/beacon_frames`. Sends world-state JSON (~10 Hz) and a downscaled JPEG (~5 fps) over UDP to the laptop. Never writes shm, never talks to `guided`. Killing it must not change what the wearer hears.

JSON format: [`laptop/samples/`](../laptop/samples/).
