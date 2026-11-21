# percept

Owner: Nathan. C++, cores 1-3 (`0xe`), `SCHED_RR` 22. YOLOE-26n, Depth Anything V2, MediaPipe hands, unproject, VO. Writes `/beacon_depth` and the percept-owned part of `/beacon_world`. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5, §7, §8.

Laptop stand-in: `tools/probe_frame.py`. It is Python and runs on a laptop only. It checks letterbox inverses, full-frame landmark 8, and metric depth before any QNX code is written.

Shm reader: `src/head.cpp` builds as `percept-head`. It reads the newest `/beacon_frames` slot, prints the YOLO and depth letterbox affines, and initialises only the ABI fields of `/beacon_depth` and `/beacon_world`. No model runs yet. It writes no detections, depth, hand, or pose data.

Build and check with `camd` running:

```sh
cd camd && make && ./camd --stub --once && cd ../percept && make && ./percept-head --once
```
