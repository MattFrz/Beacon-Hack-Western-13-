# Loaner Pi bring-up log

Status: scaffold. No device observations recorded yet.

Follow [`nathans-revision.md`](nathans-revision.md) §21 and the commands in
[`pi-dev-workflow.md`](pi-dev-workflow.md). Record what the device actually says,
with dates. Do not copy expected values here as if they were measured. Do not
put Wi-Fi credentials, PSKs, or `sd-stage/` contents in this file.

## Device facts

| Item | Observed value | Where observed | Date |
| --- | --- | --- | --- |
| SSH alias / address | `ssh qnxpi` -> `qnxuser@10.80.55.25` | `~/.ssh/config` and workflow notes | |
| Hostname | | `hostname` / `pidin` | |
| RAM | | `cat /proc/meminfo` or QNX equivalent | |
| Image / build date | | QSTI splash or package list | |
| Active cooler fitted | | visual check | |
| Thermal node | | `/dev/thermal` or image equivalent | |
| `qnxuser` password changed | | interactive `passwd` on device | |
| Default VNC password changed | | QSTI UI / device notes | |

## 1. First boot

- [ ] Let QSTI updates finish. Do not interrupt the first boot.
- [ ] Confirm SSH key login works.
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
| C270 USB | | | | | | |
| Camera Module 3 CSI | | | | | | |

Focus-lock gate: record the exact command and result. If focus cannot lock,
write that down before trying calibration.

## 4. USB audio

- [ ] Play one WAV through the USB headset.
- [ ] Record two seconds from the USB mic.
- [ ] Confirm there is no 3.5 mm playback path on this image.
- [ ] Save the device names shown by the audio tools.

| Device | Role | Name / path observed | Result |
| --- | --- | --- | --- |
| USB headset | playback | | |
| USB headset | capture | | |
| 3.5 mm | playback | | not present / present |

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
