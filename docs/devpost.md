# Beacon: a homing cue for a named item, on QNX

Blind and low-vision people often wait for someone nearby to help find a lost item. A cane does not locate things across a room. Tags only find what was tagged. Remote-help apps need a person on the line.

Beacon works from a device on the wearer's chest. The wearer asks for an item they have seen in this session, such as keys or a bottle. The device gives a short spoken bearing, and the wearer walks toward it. Once the object is close, stereo ticks speed up and pan toward it, and a steady tone marks the spot. Camera capture, detection, depth, guidance, and audio all run on a Raspberry Pi 5 under QNX 8.0.

Perception is allowed to fail. Guidance is not. Beacon runs them as separate processes. When perception dies, the guidance process keeps its audio deadline. It holds the last cue, then says it lost the target. It does not guess a distance.

## How QNX is used

Guidance runs at `SCHED_FIFO` priority 58 on core 0. Perception and the ingest relay run on other cores. Processes share state through seqlocked, newest-wins shared memory, so the audio thread never waits for a model. A supervisor at priority 63 sends a 50 ms heartbeat and respawns any child that stops responding.

Measured on the loaner Pi 5:

- In a full loop with real detection and depth on the Pi, fed a recorded clip, guidance ran 1500 periods at 16.67 ms with 0 missed. Worst lateness was 4.7 ms, p95 1.9 ms.
- We killed `ingest`, the process that writes perception results to shared memory, while guidance was running. Guidance said "I lost the target" and kept its deadline across 1800 loops with 0 missed. A new `ingest` restored the cue without restarting `guided`: 2100 loops, 0 missed, p95 2.05 ms.
- We killed `guided` under the supervisor. The fault is logged and the process respawns in about 100 ms. The device did not reboot.
- Camera frames come through QNX's Sensor Framework, the camera API that the laptop does not have.

This image accepts only single-CPU runmasks, so perception runs on one core, not spread across three. The numbers above use the masks the kernel reports back.

## On-device AI

- `onnxruntime` 1.24.4 and `opencv` 4.12.0, from QNX's open-source repository, `repo.oss.qnx.com`.
- YOLOE-26n, detect-only, with a baked noun list: 62 to 65 ms per frame when warm, at 320 px.
- Depth Anything V2 metric indoor small: 456 to 483 ms per frame.
- The image's `python3-onnxruntime` has no Python binding. `percept/ort_capi.py` calls the ONNX Runtime C API through ctypes, using 415 generated members.

## What we have not shown

We are a sighted hackathon team. Nobody who is blind or has low vision has tested this. That testing is the next step, and we want it led by blind people.

- Spoken distance. The depth scale is not checked against a tape measure on this camera, so the demo gives direction and ticks, not a number.
- Hand tracking. The MediaPipe binding fails on this image. The reach cue has run on recorded input, not on live hand position.
- Microphone. The C270 microphone does not capture on this image, so a FIND request arrives as a record, not as speech.
- Vocabulary. Six baked nouns.
- Obstacles, stairs, and traffic. Beacon does not detect them. It is a supplement to a cane.
- Live kill of the perception process. We have rehearsed the `ingest` kill, not yet the perception kill.

## What comes next

Testing with blind and low-vision wearers, paid and led by them. A tape-measure check of depth at 0.5, 1, and 2 metres, so spoken distance can be used or dropped on evidence. Hand tracking working on the device. Microphone capture working on the device.

## Built with

QNX 8.0 on Raspberry Pi 5, a Logitech C270, and a JBL Go 3 over Bluetooth. `onnxruntime` 1.24.4 and `opencv` 4.12.0 from `repo.oss.qnx.com`. YOLOE-26n (baked ONNX) and Depth Anything V2 metric indoor small. whisper.cpp is in the repo but not in the live loop. The laptop dashboard is a read-only monitor, built with Vite, React, and react-three-fiber.
