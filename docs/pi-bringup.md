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

## 4. Audio output

- [x] Confirm there is no 3.5 mm playback path on this image.
- [x] Confirm `io-snd` sees a USB control but no PCM playback device.
- [x] Play WAV clips through the JBL Go 3 over a user-space BTstack A2DP bridge.
- [ ] Play one WAV through a USB headset (still needed for the low-risk path).
- [ ] Record two seconds from a USB mic (still needed; only the C270 is attached).

| Device | Role | Name / path observed | Result |
| --- | --- | --- | --- |
| USB headset | playback | none found | no USB device enumerated |
| USB headset | capture | none found | C270 mic not attached |
| 3.5 mm | playback | no 3.5 mm jack | absent, as expected on Pi 5 |
| Audio control | control | `/dev/snd/controlC0` | present; no PCM device found |
| JBL Go 3 | A2DP playback | `18:90:67:DE:BC:EF`, name `JBL Go 3` | SBC 44.1 kHz stereo, audible tone and chime confirmed 2026-11-21 |

### 4a. Bluetooth A2DP bridge (validated 2026-11-21)

Stock QNX 8.0 has no A2DP stack and no Bluetooth HCI service. The experimental
[`Combadge-HTN/qnx-bluetooth`](https://github.com/Combadge-HTN/qnx-bluetooth)
project ports BTstack to the Pi 5's onboard BCM7271 BT UART and exposes A2DP
source playback through a named pipe. This is an **application-level output**,
not a SALSA device or system-wide route.

Staged on the Pi at `/data/home/qnxuser/projects/qnx-bluetooth` (no `.git`, no
files added to this repo). Upstream only auto-connects to a device named
`TWS Mini Speaker`; our local copy of
`btstack-master/example/a2dp_source_demo.c` was patched to also accept
`JBL Go 3`. That patch lives only on the Pi.

Setup and verification:

```sh
ssh qnxpi
cd /data/home/qnxuser/projects/qnx-bluetooth

# Read-only board and factory-address check (passed):
sudo ./btstack-master/port/qnx-pi5/a2dp_source_demo --check-board
# Pi 5 factory Bluetooth address: 88:A2:9E:A9:D4:D6

# Build (native cc on the Pi) and fetch verified radio firmware:
(cd btstack-master/port/qnx-pi5 && make -j2)
sh fetch-firmware.sh   # BCM4345C0.hcd, SHA-256 verified

# Terminal 1: start the temporary radio session.
# 'a' scans/connects, 'f' opens the PCM FIFO, 'x' plays a quiet 3 s tone.
sudo env QNX_PCM_VOLUME_SHIFT=0 sh ./run-radio.sh

# Terminal 2: play a Beacon clip after 'f'.
python3 /path/to/beacon/guided/bt_speaker.py sounds/ahead.wav
```

The FIFO contract is **44100 Hz, 2 channels, signed 16-bit little-endian**,
stereo frames of four bytes, one writer at a time. Use
`QNX_PCM_VOLUME_SHIFT=0` for speech; the default divides by 32. `audio.pcm`
must exist (`mkfifo -m 600 audio.pcm`). `guided/bt_speaker.py` converts the
16 kHz mono clips in `sounds/` to this format using only the Python standard
library.

Observed on 2026-11-21:

- Board check passed. GPIO 24–27 and 29 were `pull=pd func=INPUT`, matching
  the launcher's guard; GPIO 28 (WL_ON) was left alone.
- JBL discovered at RSSI −35 dBm, paired, negotiated SBC 44100 Hz stereo and
  established the A2DP stream plus AVRCP. Reconnected from stored pairing on
  the next run without pairing mode.
- Quiet built-in tone audible and confirmed by user.
- `play_pcm.py` sent a 44.1 kHz stereo chime; receiver reported
  `PCM stopped: 63945 input frames` at gain 1/1. Audible and confirmed by user.
- On Ctrl-C, GPIO/UART returned to the idle baseline and `.radio-lock` was
  removed. No boot image, system config, or startup service was changed.

Caveats, keep them visible:

- Experimental: three upstream commits, short tests only, no long-duration or
  reconnect stress test, polled UART backend, one historical link-supervision
  timeout reported upstream.
- Requires root and direct GPIO/MMIO access. The launcher is guarded for a
  specific BCM2712 D0 board; do not bypass its checks.
- SSP confirmation still prints a TODO, but the handler rejects any address
  other than `device_addr`; auto mode pins that to the JBL's address.
- No system-wide audio route: QNX SALSA here has no external PCM plugin, and
  the available `io-snd` driver interface is not available in this image.
- BTstack's free license is personal/non-commercial. Do not vendor it into a
  commercial build.
- Not on the 16 ms tick path. Keep GPIO piezo as the cannot-fail cue.

### 4b. Supervisor-managed Bluetooth child (validated 2026-11-21)

`supervisor/bt_audio_service.sh` is the child Beacon's supervisor should start
as root. It runs `run-radio-auto.sh` in a restart loop and logs to
`bt_audio.log`. It does **not** install anything in QNX boot config.

The Pi-side qnx-bluetooth copy has local-only patches: accept `JBL Go 3` in the
name filter; `QNX_AUTO` mode connects to a pinned `QNX_BT_ADDR`, opens
`audio.pcm`, and calls `a2dp_source_start_stream()` itself; a two-second timer
reconnects after A2DP release; the launcher cleans UART registers and stale
locks on exit. Pinned address: `18:90:67:DE:BC:EF`. The stock upstream binary
was rebuilt and tested separately to confirm radio failures were not caused by
these patches.

```sh
# Started by supervisor (root), not by /boot/onboot:
sudo sh /data/home/qnxuser/projects/qnx-bluetooth/bt_audio_service.sh

# Playback while the service is up:
python3 guided/bt_speaker.py sounds/ahead.wav
```

Validated after a Pi reboot: no key presses; service auto-connected to the
JBL, opened the FIFO at gain 1/1, started the stream, and consumed all 63,945
frames of the 16 kHz → 44.1 kHz converted chime. `pairings.tlv` survived the
reboot. On a clean TERM/HUP, GPIO, UART and `.radio-lock` are restored.

Boot persistence is installed in `/usr/etc/startup/post_startup.sh`, after the
`io-snd` block and before the final `exit 0`. The guarded snippet runs:

```sh
on -d -p 10 sh /data/home/qnxuser/projects/qnx-bluetooth/bt_audio_service.sh \
    >/dev/null 2>&1 </dev/null
```

Backup:
`/data/home/qnxuser/beacon-backups/post_startup.sh.20261121T160026Z`.
Rollback is to copy that backup back over `post_startup.sh` and reboot. The
first log line after boot may show `1970-01-01T00:00:10Z` because the service
starts before time sync; that is cosmetic.

Verified 2026-11-21 16:00 UTC: after `sudo shutdown -f` and SSH returning,
`pidin ar` showed the service, launcher and radio process with no manual
launch; the log showed `Auto-connecting`, `PCM FIFO ready (auto)` and
`Stream started`. GPIO staying in ALT4 is expected while the radio is active.

If an aborted session leaves the radio claimed, with no radio process running:

```sh
cd /data/home/qnxuser/projects/qnx-bluetooth
sudo gpio-bcm set 29 op dl pd
sudo gpio-bcm set 24-27 ip pd
sudo gpio-bcm set 29 ip pd
sudo rm -rf .radio-lock
sudo ./uart_probe --idle-after-abort
```

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
| 2026-11-21 15:07 UTC | BTstack board check | Cloned `Combadge-HTN/qnx-bluetooth` to `/tmp`, copied 43 MB without `.git` to `qnxpi:/data/home/qnxuser/projects/qnx-bluetooth`, built natively with `make -j2`. Read-only `--check-board` passed with Bluetooth address `88:A2:9E:A9:D4:D6`. GPIO baseline matched the launcher guard. No radio session started yet. |
| 2026-11-21 15:11 UTC | BT firmware | `fetch-firmware.sh` downloaded `BCM4345C0.hcd` (63806 bytes) and verified SHA-256 `51c45e77ddad91a19e96dc8fb75295b2087c279940df2634b23baf71b6dea42c`. |
| 2026-11-21 15:14 UTC | BT scan, no JBL | Short radio session initialized the controller at 3 Mbps and scanned, but saw only a phone named `me`; the JBL was not in pairing mode. Clean exit restored GPIO/UART and removed `.radio-lock`. |
| 2026-11-21 15:16 UTC | JBL A2DP tone | Patched the demo's speaker-name filter locally to accept `JBL Go 3`. With the speaker in pairing mode: found `18:90:67:DE:BC:EF` at −35 dBm, paired, negotiated SBC 44100 Hz stereo, established A2DP/AVRCP, played the quiet 3 s tone. User confirmed audible. Clean exit restored hardware state. |
| 2026-11-21 15:18 UTC | Bluetooth PCM playback | Created `audio.pcm`, generated a 63945-frame 44.1 kHz stereo chime, and ran `play_pcm.py` at `QNX_PCM_VOLUME_SHIFT=0` while the radio was connected. Receiver reported all 63945 frames consumed; user confirmed audible. Radio exited 130 on intentional Ctrl-C with hardware restored. |
| 2026-11-21 | Beacon backend/docs | Added `guided/bt_speaker.py` (stdlib-only 16 kHz mono → 44.1 kHz stereo WAV player) and documented the validated BT path in `docs/team-plan.md` and this file. Changes are local and uncommitted. |
| 2026-11-21 15:21 UTC | Backend playback | Played a generated 23200-frame 16 kHz mono chime through `guided/bt_speaker.py`; the Pi converted it to 63945 stereo frames and the JBL stream consumed all of them. User confirmed audible. |
| 2026-11-21 15:27–15:41 UTC | Supervisor child bring-up | Added `supervisor/run-radio-auto.sh` and `supervisor/bt_audio_service.sh` with pinned auto-connect, auto FIFO, reconnect timer and cleanup. An SSH hangup left the BT controller wedged; the stock upstream binary failed identically, so the auto patches were not the cause. Recovered GPIO/UART with `uart_probe --idle-after-abort`. |
| 2026-11-21 15:42 UTC | Pi reboot | Rebooted with `sudo shutdown -f` (QNX shutdown defaults to reboot; `-r` is invalid). GPIO/UART came back idle and `pairings.tlv` survived. |
| 2026-11-21 15:47 UTC | Auto service validated | With the QNX_AUTO binary restored after the stock test: supervisor child connected to `18:90:67:DE:BC:EF` without key presses, opened `audio.pcm` at gain 1/1, started the stream, and consumed 63945 frames. Hardware was restored manually after the SSH test session hangup. |
| 2026-11-21 15:52 UTC | Detached launch | Relaunched the service with QNX `on -d -p 10` so it survives SSH disconnect. Confirmed the service, launcher and radio process remained after the launching SSH session closed, with the JBL connected and stream started. |
| 2026-11-21 16:00 UTC | Boot persistence | Added a guarded detached launch to `/usr/etc/startup/post_startup.sh` after `io-snd`; backup saved under `/data/home/qnxuser/beacon-backups/`. Rebooted with `sudo shutdown -f`; service started automatically, reconnected to the pinned JBL, opened the FIFO and started the stream with no manual steps. |
| 2026-11-21 16:40 UTC | 32-label YOLOE re-export | Re-exported `models/yoloe26n_320.onnx` from `/tmp/beacon-model-export/yoloe-26n-seg.pt` after expanding `labels.txt` to 32 names. Output shape `(1, 36, 2100)`, SHA-256 `5953c2a71da1f013083e6659066a27b23af3c783ec198e75120196609a65471b`. ORT probe on `bus.jpg` found `person` at 0.81/0.80/0.72/0.27 (`--conf 0.15`) and `shoes` at 0.20/0.19. Combined with metric depth and `--fov`, person `xyz_cam` Z was 6.1 to 10.4 m. The ONNX stays gitignored. Runtime packages are still missing on QNX. |
| 2026-11-21 23:24 UTC | `ingest` built natively on QNX | Repo synced to `/data/home/qnxuser/Beacon-Hack-Western-13-/`; `make -C ingest` needed `-lsocket` for `recvfrom` (fixed in the Makefile's QNX branch). `make -C guided` built clean as shipped. |
| 2026-11-21 23:28 UTC | Guidance loop end-to-end on QNX | `ingest --udp` + `guided` on the loaner (no camera, no model): guided said a WALK cue ("keys ahead"), entered REACH (ticks, then tone), went HOLD after the record stream stopped, then spoke "I lost the target". `SCHED_FIFO 58` applied as unprivileged `qnxuser` (no `procmgr_ability` needed at this priority). 780 loops, **0 missed 16 ms deadlines**, worst lateness ~1.0 ms, 0 speech drops. This is plan step 4 (`docs/qnx-integration-plan.md`) green on the device. |
| 2026-11-21 23:27 UTC | Kokoro TTS verified on device | llama.cpp upstream `e6d624b` + Kokoro-82M F32 (native build at `/data/home/qnxuser/llama`, done earlier tonight): `bin/kokoro -p "Keys. About two metres ahead, a little left."` wrote a 3.05 s WAV in 15.9 s compute (0.19x realtime). Pre-render the clip set on the Pi; never generate on the 16 ms path. An `oss.qnx.com`-catalog AI module is now producing output on the loaner. |
| 2026-11-22 ~00:00 UTC | QNX apk repo discovery | `repo.oss.qnx.com` is QNX's own **apk (apk-tools) repository**, directly fetchable over https — no QDD UI needed for the packages it carries. Indexes: `8.0.3/core+extra` (opencv 4.12, python3-opencv, mediapipe 0.10.26, python3-numpy 2.4.1, tflite-runtime, llama.cpp), `8.0.5/core+extra` (**onnxruntime 1.24.4 + python3-onnxruntime**, **whisper.cpp 0_git20260729**), all aarch64. `apk-tools 3.0.0_rc5` itself is packaged there. Officially-unpackaged QSC deps (`qnx-crypto`, `qnx-io-sock`) are declared by some packages but appear in **no ELF NEEDED list** of the AI stack (readelf-verified on the laptop). |
| 2026-11-22 ~00:15 UTC | apk bootstrap attempt on loaner | `apk --root /data/home/qnxuser/oss --force-no-chroot add --initdb --usermode` runs, but resolution blocks on `qnx-crypto`/`qnx-io-sock` (QSC-only, absent from the public repo). Local dummy-package repos were not read in any form (dir/file:///loopback-HTTP, v2+v3 index formats). **Decision: install by archive extraction instead** (openqnx method 2B): `percept/tools/qnx_pkg_fetch.py` resolves the dep closure from the APKINDEX files and downloads every `.apk`; they are plain signed tars. |
| 2026-11-22 ~00:30 UTC | AI stack staged (laptop), transfer interrupted | Closure: **232 packages, 225 MB download, 661 MB / 9597 files extracted** (onnxruntime+python3-onnxruntime, opencv+python3-opencv, python3-mediapipe, python3-numpy, whisper.cpp incl. `whisper-cli`, absl/protobuf/re2/flatbuffers/icu/libc++/libunwind...). `readelf` check: everything the stack links is in the closure or the base image; only `libregex.so.1` is not in any index (QNX base lib; verify on device). Pi rebooted mid-transfer and left the hotspot; `airoot/` staged locally at `/tmp/qnx-ai-root` with per-package file lists, ready to rsync when the Pi is back. On-device gate: `ingest/tools/ai-import-test.sh`. |
