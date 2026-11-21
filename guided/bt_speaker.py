#!/usr/bin/env python3
"""Minimal Beacon backend for playing a WAV on the Bluetooth speaker.

The QNX Pi 5 has no system-wide A2DP output. The experimental qnx-bluetooth
project exposes a named pipe instead; this module converts Beacon's 16 kHz mono
clips to that pipe's 44.1 kHz stereo S16LE format and writes with backpressure.

Radio session (run on the Pi, in its own terminal):

    cd /data/home/qnxuser/projects/qnx-bluetooth
    sudo env QNX_PCM_VOLUME_SHIFT=0 sh ./run-radio.sh
    # press 'a' to connect, then 'f' to open audio.pcm

Playback (any terminal on the Pi):

    python3 guided/bt_speaker.py sounds/ahead.wav

This is an application-level bridge, not a SALSA device. `guided` should keep
its piezo path as the cannot-fail cue. Import play_wav() if a larger audio
backend wants to call it; this script never opens USB audio itself.
"""

from __future__ import annotations

import argparse
import errno
import os
import select
import stat
import struct
import time
import wave
from pathlib import Path

DEFAULT_FIFO = Path("/data/home/qnxuser/projects/qnx-bluetooth/audio.pcm")
TARGET_RATE = 44100
FRAME_BYTES = 4          # stereo S16LE
CHUNK_FRAMES = 441       # 10 ms at 44.1 kHz


def _mono_samples(path: Path) -> tuple[list[int], int]:
    """Read a PCM WAV and return mono samples plus its source rate."""
    with wave.open(str(path), "rb") as source:
        if source.getcomptype() != "NONE":
            raise ValueError("WAV must be uncompressed PCM")
        if source.getsampwidth() != 2:
            raise ValueError("WAV must be 16-bit PCM")
        channels = source.getnchannels()
        rate = source.getframerate()
        raw = source.readframes(source.getnframes())

    if len(raw) % 2:
        raise ValueError("WAV has a truncated sample")
    values = struct.unpack("<%dh" % (len(raw) // 2), raw)
    if channels == 1:
        return list(values), rate
    if channels == 2:
        return [
            (values[i] + values[i + 1]) // 2
            for i in range(0, len(values) - 1, 2)
        ], rate
    raise ValueError("WAV must be mono or stereo")


def _resample(samples: list[int], src_rate: int) -> list[int]:
    """Linear interpolation; no third-party packages on the QNX image."""
    if not samples or src_rate == TARGET_RATE:
        return samples
    out_len = int(round(len(samples) * TARGET_RATE / src_rate))
    out = []
    for i in range(out_len):
        pos = i * src_rate / TARGET_RATE
        i0 = min(int(pos), len(samples) - 1)
        i1 = min(i0 + 1, len(samples) - 1)
        frac = pos - i0
        out.append(int(samples[i0] * (1 - frac) + samples[i1] * frac))
    return out


def pcm_chunks(path: Path, chunk_frames: int = CHUNK_FRAMES):
    """Yield 44.1 kHz stereo S16LE byte chunks with complete frames."""
    mono, rate = _mono_samples(path)
    stereo = _resample(mono, rate)
    for start in range(0, len(stereo), chunk_frames):
        chunk = bytearray()
        for sample in stereo[start:start + chunk_frames]:
            chunk.extend(struct.pack("<hh", sample, sample))
        yield bytes(chunk)


def send_pcm(chunks, fifo: Path = DEFAULT_FIFO, timeout: float = 10.0) -> None:
    """Write chunks to audio.pcm, waiting for the radio and respecting backpressure."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
            break
        except OSError as exc:
            if exc.errno != errno.ENXIO or time.monotonic() >= deadline:
                raise
            time.sleep(0.05)

    try:
        if not stat.S_ISFIFO(os.fstat(fd).st_mode):
            raise ValueError("%s must be a named pipe" % fifo)
        for chunk in chunks:
            if len(chunk) % FRAME_BYTES:
                raise ValueError("chunks must contain complete stereo frames")
            pending = memoryview(chunk)
            deadline = time.monotonic() + timeout
            while pending:
                try:
                    written = os.write(fd, pending)
                    pending = pending[written:]
                    deadline = time.monotonic() + timeout
                except BlockingIOError:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Bluetooth PCM receiver stopped consuming")
                    select.select([], [fd], [], min(remaining, 0.25))
    finally:
        os.close(fd)


def play_wav(path: Path, fifo: Path = DEFAULT_FIFO) -> int:
    """Play one WAV; return the number of stereo frames submitted."""
    submitted = 0

    def counted():
        nonlocal submitted
        for chunk in pcm_chunks(path):
            submitted += len(chunk) // FRAME_BYTES
            yield chunk

    send_pcm(counted(), fifo)
    return submitted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path, help="16-bit PCM WAV, mono or stereo")
    parser.add_argument(
        "--fifo", type=Path, default=DEFAULT_FIFO,
        help="qnx-bluetooth audio.pcm path (default: %(default)s)",
    )
    args = parser.parse_args()
    frames = play_wav(args.wav, args.fifo)
    print("submitted %d stereo frames to %s" % (frames, args.fifo))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TimeoutError) as exc:
        raise SystemExit(str(exc))
