# camd

Owner: Nathan. C, core 0 (`0x1`), `SCHED_FIFO` 50. Sensor Framework into the newest-wins three-slot `/beacon_frames` ring. No colour convert, no models. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §5.1, §6.

## Current state

The shm ring, seqlock writes, core 0 pinning, and FIFO priority are implemented. The camera source is a synthetic BGR8888 frame for the laptop and for QNX scheduler wiring. The QNX CamAPI adapter is not wired yet. `frametype = 0` is a stub marker and must not be frozen as a real camera frametype.

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

Check the shm ring from another shell:

```sh
./read-frames
```

On QNX, build with `qcc` and run only with `--stub` until the CamAPI adapter lands. `CAM_W`, `CAM_H`, `stride`, and `frametype` come from the camera probe, never from this stub.
