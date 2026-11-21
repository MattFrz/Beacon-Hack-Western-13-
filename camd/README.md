# camd

Owner: Nathan. C, core 0 (`0x1`), `SCHED_FIFO` 50. Sensor Framework into the newest-wins three-slot `/beacon_frames` ring. No colour convert, no models. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1, §6.

## Current state

The shm ring, seqlock writes, core 0 pinning, and FIFO priority are implemented. The camera source is either a synthetic BGR8888 frame or a bring-up-only uncompressed 32-bit BMP file. The QNX CamAPI adapter is not wired yet. `frametype = 0` is a stub marker and `frametype = 65535` is the BMP bring-up marker; neither may be frozen as a real camera frametype.

`include/beacon.h` on this branch is Munadir's draft, marked DRAFT and waiting for Matt's sign-off. Do not call the ABI frozen.

## Build and check

On the laptop:

```sh
cd camd
make
./camd --stub --once
```

With the full stub loop:

```sh
./camd --stub --hz 30 --frames 90
```

To publish a screenshot from a C270 JPEG feed as a real-pixel frame-source test:

```sh
./camd --bmp /tmp/c270-frame.bmp --once
./read-frames
```

This reads a top-down or bottom-up 32-bit BMP with BI_RGB or standard BGRA
BI_BITFIELDS masks. It publishes the BMP's own width, height, stride, and a
bring-up-only frametype marker. It is not a camera driver and does not set
`CAM_W`, `CAM_H`, or the eventual camera frametype.

Check the shm ring from another shell:

```sh
./read-frames
```

QNX deadline check with hogs on cores 1-3:

```sh
./deadline-test --hogs 3 --samples 1800
```

The output keeps several counters separate. `over_1ms` is jitter against a
1 ms clock; QNX reports `clock_getres(CLOCK_MONOTONIC)` as 0.001 s on this Pi.
`over_period` is the useful missed-deadline count because the guided period is
16.667 ms. Do not call `over_1ms` a missed 16 ms deadline.

On QNX, build with `qcc` and run only with `--stub` until the CamAPI adapter lands. `CAM_W`, `CAM_H`, `stride`, and `frametype` come from the camera probe, never from this stub.
