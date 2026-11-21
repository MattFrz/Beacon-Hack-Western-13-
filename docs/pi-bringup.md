# Loaner Pi bring-up log

Status: observations started on 2026-11-21. Camera capture, audio loopback, GPIO, and scheduler measurements are still open.

Follow [`nathans-revision.md`](nathans-revision.md) §21 and the commands in
[`pi-dev-workflow.md`](pi-dev-workflow.md). Record what the device actually says,
with dates. Do not copy expected values here as if they were measured. Do not
put Wi-Fi credentials, PSKs, or `sd-stage/` contents in this file.

## Device facts

| Item | Observed value | Where observed | Date |
| --- | --- | --- | --- |
| SSH alias / address | `ssh qnxpi` -> `qnxuser@10.80.55.25` | `~/.ssh/config` and workflow notes | 2026-11-21 |
| Hostname | `qnxpi` | `hostname` on device | 2026-11-21 13:51 UTC |
| RAM | `pidin info`: free 7483 MB / 8128 MB | `pidin info` | 2026-11-21 13:51 UTC |
| Image / build date | `QNX qnxpi 8.0.0 2026/06/05-16:21:14EDT RaspberryPi5 aarch64le` | `uname -a` | 2026-11-21 13:51 UTC |
| CPUs | 4 x Cortex-A76 at 1500 MHz | `pidin info` | 2026-11-21 13:51 UTC |
| Active cooler fitted | reported by team inventory; not rechecked | teammate inventory | 2026-11-21 02:30 |
| Thermal node | `/dev/thermal` and `/dev/thermal_ext` exist | `ls -l /dev/thermal*` | 2026-11-21 13:51 UTC |
| Clock resolution | `clock_getres`: monotonic 0.001 s, realtime 0.001 s | Python `time.clock_getres` | 2026-11-21 13:55 UTC |
| `qnxuser` password changed | not checked | interactive `passwd` on device | |
| Default VNC password changed | not checked | QSTI UI / device notes | |

## 1. First boot

- [ ] Let QSTI updates finish. Do not interrupt the first boot.
- [x] Confirm SSH key login works.
- [ ] Change the `qnxuser` password interactively on the device.
      `passwd` cannot be fed over a piped SSH session.
- [ ] Change the default VNC password.

```sh
ssh qnxpi
# on the device:
passwd
```

## 2. Packages

Install from `oss.qnx.com` with the QDD package UI or the image package tool.
On this image `pkginfo`, `pkgadd`, and `pkgremove` are absent. `apkgrel` is the
only obvious package-named binary in `/usr/bin`. Python 3.14 and `pip` 25.1.1
are present, but no CV/ML Python packages were found. PyPI did not provide a
QNX wheel for numpy 2.5.5; pip fell back to a source build and failed in Meson
with `Cython requires python3 dependency for link testing`. Use QNX ports or
`oss.qnx.com` binaries, not plain PyPI wheels, for the native packages. The
`qnx-ports/build-files` catalog lists `onnxruntime`, `opencv`, `numpy`, and
`pytorch`, but those are source build files for a Linux host with QNX SDP. No
prebuilt binary was installed on the Pi from that route.

Record the exact package name and version shown by the tool. The research
versions below are targets, not observations.

| Package | Research version | Installed package name | Installed version | Used by |
| --- | --- | --- | --- | --- |
| `onnxruntime` | 1.24.4 | | | YOLOE-26n, Depth Anything V2 |
| `tflite-runtime` | 2.21.0 | | | hands |
| `mediapipe` | 0.10.26 | | | hands |
| `opencv` | 4.12.0 | | | letterbox, ORB, PnP |
| `whisper.cpp` | 2026-07 git | | | `voiced` |
| `llama.cpp` | 0.0.9006 | | | table-miss remap only |

After inference runtimes are installed:

```sh
ssh qnxpi 'pidin ar > /data/home/qnxuser/app/pidin-packages.txt'
```

Check that no `percept` worker thread has CPU 0 in its runmask. Pin runtime
thread pools to cores 1-3.

## 3. Camera probe

Do this with the C270 if Camera Module 3 has not arrived. Keep USB and CSI
results in separate rows. Do not write C270 dimensions into `include/beacon.h`.

Camera config sources:

```sh
ssh qnxpi 'cat /etc/config/sensor/sensor_rpi5.conf'
ssh qnxpi 'grep -n sensor /usr/etc/startup/post_startup.sh'
```

Capture one uncompressed frame with the QNX AI Camera App or a small CamAPI
probe. Save the frame under `/data/home/qnxuser/`, not in git.

| Camera | Unit number | `W x H` | Frametype | Focus lock possible | Frame saved to | Date |
| --- | --- | --- | --- | --- | --- | --- |
| C270 USB | unit 5 in shipped config; unit 1 with temporary JPEG config | 640 x 480 configured | JPEG only | unknown | live frame rendered and screenshotted to `/tmp/c270-frame.bmp`; not a raw sensor frame in git | 2026-11-21 14:35 UTC |
| Camera Module 3 CSI | units 3 and 4 configured as `imx708` | 2304 x 1296 configured | `nv12` configured | unknown | no frame | 2026-11-21 13:52 UTC |

`/etc/config/sensor/sensor_rpi5.conf` defines simulator units 1 and 2, USB
units 5 to 7, and ISP tuning for units 3 and 4. Plain `pidin ar` as `qnxuser`
only lists the user's own processes; use `sudo pidin ar` to see the Sensor
service. The shipped C270 entry is unit 5, but the camera only lists JPEG
formats in `mjpeg_example -l`; `camera_example1_callback` forces ycbycr and
returns `Failed in call to read: err = 25 numbytes 0`.

A temporary `/tmp/beacon_sensor_mjpeg.conf` starts unit 1 with
`default_video_format = jpeg`. With Sensor restarted from that config,
`mjpeg_example` reports `CAMERA_STATUS_CONNECTED` and renders the live camera.
`sudo screenshot -file=/tmp/c270-frame.bmp` saved a 1024x600 screenshot of the
displayed feed. That file is a screen capture, not the raw 640x480 JPEG frame,
and it is not committed.

Focus-lock gate is still open. `camd` has no decoded camera frames yet, so
`CAM_W`, `CAM_H`, and frametype are still unset in `include/beacon.h`. The C270
remains a bring-up fallback, not the chosen camera.

## 4. USB audio

- [ ] Play one WAV through the USB headset.
- [ ] Record two seconds from the USB mic.
- [ ] Confirm there is no 3.5 mm playback path on this image.
- [ ] Save the device names shown by the audio tools.

| Device | Role | Name / path observed | Result |
| --- | --- | --- | --- |
| USB headset | playback | none found | no USB device enumerated |
| USB headset | capture | none found | C270 mic not attached |
| 3.5 mm | playback | no 3.5 mm jack | absent, as expected on Pi 5 |
| Audio control | control | `/dev/snd/controlC0` | present; no PCM device found |

## 5. GPIO and piezo

- [ ] Blink a GPIO pin from the QNX `rpi_gpio` sample.
- [ ] If the buzzer and transistor are on hand, drive the piezo through the
      transistor. Do not drive it directly from the GPIO pin.
- [ ] Otherwise leave this unchecked until Saturday parts arrive.

## 6. Scheduler skeleton

This is spec §21 step 7. It proves the QNX story before models are added.

- [ ] `supervisor` spawns a FIFO 58 dummy `guided` pinned to core 0.
- [ ] Three `while(1)` hogs run on cores 1-3.
- [ ] Ticks stay inside 16 ms.
- [ ] Capture System Profiler / `tracelogger` output.
- [ ] Save `pidin ar` showing runmasks.

Partial result: the deployed `camd` stub built on the Pi and ran under
`sudo -n` with core 0 pinning and FIFO 50. `deadline-test` then ran 600 and
1800 wakeups at 60 Hz with one, two, and three hogs. With three hogs and 600
samples, wakeups were `p95_late_ns=6312240`, `worst_late_ns=11961423`, and
`over_period=0`. With three hogs and 1800 samples, `p95_late_ns=6902551`,
`worst_late_ns=19566706`, and `over_period=2`.

The first reading looked like a failure because the test counted anything over
1 ms as a miss. `clock_getres(CLOCK_MONOTONIC)` is 1 ms on this image, so that
count measures jitter, not missed 16.667 ms deadlines. Read `over_period` for
deadline misses. A runmask dump from `pidin` is still open.

```sh
ssh qnxpi 'pidin ar > /data/home/qnxuser/app/pidin-scheduler.txt'
ssh qnxpi 'slog2info -w'
```

## 7. Only then calibrate

Chessboard calibration must use the locked `CAM_W x CAM_H`. Save the result as
`models/calib.json` on the laptop with `fx`, `fy`, `cx`, `cy`, `W`, and `H`.
Tape-check depth at 1 m before allowing spoken metres.

Do not launch Beacon from `/boot/onboot`. Start `supervisor` from a later SLM
or `post_startup` snippet after `io-audio`, Sensor Framework, and `/usr` exist.

## Attempts and environment notes

| Time | Attempt | Result |
| --- | --- | --- |
| 2026-11-21T07:22:30-05:00 | `ssh -o BatchMode=yes -o ConnectTimeout=5 qnxpi` | `connect to host 10.80.55.25 port 22: Connection timed out`. The hotspot or device was not reachable from this laptop. |
| 2026-11-21T07:22:30-05:00 | Laptop Python import check | `cv2`, `numpy`, `onnxruntime`, `ultralytics`, `mediapipe`, `torch`, and `transformers` are not installed. `python3 -m pip --version` returned nothing. `ffmpeg` is at `/etc/profiles/per-user/nate/bin/ffmpeg`. |
| 2026-11-21 02:30 | Teammate hardware inventory | Pi 5 has active cooler; RAM size is still unconfirmed. JBL Go 3 is Bluetooth-only with no AUX, and QNX has no Bluetooth audio on this Pi, so Beacon still needs USB audio out. C270 is not on QNX's tested camera list; the §21 probe decides whether it works. Hardware workshop reopens Saturday at 12 pm. |
| 2026-11-21 08:37 | Laptop probe setup | `uv` created `/tmp/beacon-probe-venv` with Python 3.12, numpy, OpenCV, onnxruntime, and mediapipe. `percept/tools/probe_frame.py` ran on a synthetic 640x480 image. With a constant test ONNX depth model it reported a 210x210 depth grid. No real model or Pi observation was involved. |

| 2026-11-21 13:51 UTC | Pi reachable | `hostname` returned `qnxpi`; `uname -a` returned QNX 8.0.0, build 2026/06/05, RaspberryPi5 aarch64le. `pidin info` reported 8128 MB total RAM. |
| 2026-11-21 13:52 UTC | Sensor framework probe | Config read successfully. `sensor` did not persist when detached. `camera_example1_callback -u 1` returned read error 25. No USB device was enumerated. |
| 2026-11-21 13:52 UTC | Audio probe | Only `/dev/snd/controlC0` existed. No USB headset or PCM device was found. |
| 2026-11-21 13:54 UTC | Skeleton deployed to Pi | Copied `include/beacon.h`, `camd/`, and `percept/` to `/data/home/qnxuser/beacon-test`. Both built with the on-device toolchain. |
| 2026-11-21 13:54 UTC | `camd`/`percept-head` on QNX | `sudo -n ./camd --stub --once` published `frame_id=1`, 640 x 480, stride 2560, `frametype=0`, 1228800 bytes. `read-frames` saw the slot. `percept-head --once` printed the same frame and the 320 and 210 letterbox affines. |
| 2026-11-21 13:55 UTC | Deadline test on QNX | Clock resolution is 1 ms. With 0 hogs, 600 samples had `over_period=0`. With 3 hogs, 600 samples had `over_period=0`; 1800 samples had `over_period=2` and `p95_late_ns=6902551`. The 1 ms counter is jitter, not a 16 ms miss count. |
| 2026-11-21 14:02 UTC | pip install into local target | `pip3 install --target /data/home/qnxuser/beacon-test/pythonlibs numpy opencv-python-headless onnxruntime mediapipe` failed on numpy metadata generation. No QNX wheel was found; the source build failed with a Cython link-test error. No package was installed. |
| 2026-11-21 09:08 EST | Laptop YOLOE export | `percept/tools/export_yoloe.py` exported a detect-only static ONNX with all 17 labels baked. Output was 9.3 MB with shape `(1, 21, 2100)`, i.e. 2100 raw proposals with no NMS. The original Ultralytics-backed probe found people in `bus.jpg`. The ONNX stays gitignored in `models/`. |
| 2026-11-21 09:11 EST | Laptop depth export | `percept/tools/export_depth.py` exported Depth Anything V2 Metric Indoor Small to a static `(1, 3, 210, 210)` input and `(1, 210, 210)` metric output. Combined with YOLOE on `bus.jpg`, sampled depths at person centres were 6.1 to 10.3 m. Tape check still required. |
| 2026-11-21 09:13 EST | Laptop hand probe | Downloaded MediaPipe Tasks `hand_landmarker.task`. With `libglvnd` on `LD_LIBRARY_PATH`, `probe_frame.py --hands --hand-model ...` found a fingertip in the MediaPipe `woman_hands.jpg` sample. |
| 2026-11-21 14:13 UTC | Models staged on Pi | Copied YOLOE ONNX, depth ONNX plus `.onnx.data`, and `hand_landmarker.task` to `/data/home/qnxuser/beacon-test/models`. All four SHA-256 hashes match the laptop values. Runtime packages are still missing. |
| 2026-11-21 14:15 UTC | USB recheck | Still no USB device in `usb` output. `/dev/snd` still only has `controlC0`. C270 and USB audio are not attached. |
| 2026-11-21 14:24 UTC | C270 enumerated | `usb` now shows Logitech `0x046d:0x0825` C270 HD WEBCAM on USB 0. `/dev/sensor/camera5` exists. `camera_example1_callback -u 5` still returns `Failed in call to read: err = 25 numbytes 0`. No frame captured. |
| 2026-11-21 14:28 UTC | Sensor process visibility | `sudo pidin ar` shows the Sensor service already running as `sensor -U 521:521 -b external -r /data/share/sensor -c /etc/config/sensor/sensor_rpi5.conf`. Plain `pidin ar` as `qnxuser` only showed the current shell, so earlier `no-sensor` checks were not valid. New sensor instances exited; this is not yet a camera fix. |
| 2026-11-21 14:30 UTC | Raw YOLO decode and depth bounds | `probe_frame.py` now decodes the raw `(1, 21, 2100)` YOLOE output through ONNX Runtime with letterbox, inverse, and NMS. It detected four people in `bus.jpg`; combined with depth, sampled Z was 6.1 to 10.4 m. Fixed a right-edge `depth_at_full` index bug found by review. |
| 2026-11-21 14:35 UTC | Live C270 frame | C270 exposes JPEG only: `mjpeg_example -l` lists JPEG at 640x480 and other sizes. `camera_example1_callback` forces ycbycr and still fails with err 25. Restarted Sensor with a temporary `/tmp/beacon_sensor_mjpeg.conf` using `default_video_format = jpeg`; `mjpeg_example` reported `CAMERA_STATUS_CONNECTED`, decoded JPEG, and rendered a live scene. `sudo screenshot -file=/tmp/c270-frame.bmp` captured it. This proves camera capture; it is not yet a raw frame in `/beacon_frames` and does not freeze C270 geometry in `include/beacon.h`. |
| 2026-11-21 14:39 UTC | Probe on live C270 screenshot | Copied a second `mjpeg_example`/`screenshot` BMP to the laptop and ran `probe_frame.py` on it. Raw ORT YOLOE found `person` at 0.30 with `--conf 0.15`. This is a display screenshot, still not a raw `/beacon_frames` frame. |
| 2026-11-21 14:40 UTC | Uncompressed format probe | Restarted Sensor with `nv12`, `rgb8888`, and `ycbcr420p` configs; `camera_example1_callback -u 1` still returned err 25. Restored the working JPEG config. C270 has no usable uncompressed path for the current `camd` reader. |
| 2026-11-21 14:42 UTC | Demo-class image probes | Raw ORT YOLOE detected `bottle` at 0.36/0.29 in a PET bottle image. It detected `keychain` at 0.166 in a car-keys image only when `--conf` was lowered to 0.15; default 0.25 missed it. Real demo objects still need a live C270 probe before picking a confidence threshold. |
| 2026-11-21 14:50 UTC | BMP frame source | Added `camd --bmp PATH` as a bring-up-only real-pixel source. It reads 32-bit BMPs, including the QNX screenshot's top-down BGRA BI_BITFIELDS format, and publishes the BMP's own dimensions with frametype marker 65535. Verified on the laptop with `/tmp/c270-frame.bmp`: `read-frames` saw 1024x600, stride 4096, 2457600 bytes. This is not a camera driver and does not set `CAM_W`, `CAM_H`, or a real camera frametype. |
| 2026-11-21 15:39 UTC | QNX shm round-trip | Deployed the new `camd`, `read-frames`, and `dump-frame` to `/data/home/qnxuser/beacon-test/camd` and built them with the on-device `cc`. Captured a fresh C270 JPEG feed with `mjpeg_example` + `screenshot` to `/tmp/c270-qnx-frame.bmp`. On QNX, `camd --bmp` published it to `/beacon_frames`; `read-frames` saw frame_id 1, 1024x600, stride 4096, frametype 65535, 2457600 bytes. `dump-frame` wrote `/tmp/c270-qnx-roundtrip.bmp`; the laptop probe found `person` at 0.20 with `--conf 0.15` (default 0.25). This is a screen-capture round-trip, not a raw camera frame in camd. |
