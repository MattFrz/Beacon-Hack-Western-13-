"""Make every Beacon voice clip with tiny-voca (offline, Apache-2.0).

tiny-voca: https://huggingface.co/n4ze3m/tiny-voca (4.5M params, voices F2/M2).
Runs once on a laptop (Linux / WSL); Beacon only plays the finished WAVs.

Setup:
    python3 -m venv /opt/tts
    /opt/tts/bin/pip install onnxruntime soundfile numpy huggingface_hub \
        git+https://github.com/n4ze3m/dizione
    /opt/tts/bin/hf download n4ze3m/tiny-voca onnx/model.onnx config.json \
        --include "phonemizer/*" --local-dir /opt/tiny-voca
    sudo apt install ffmpeg

Run:
    DIZIONE_DATA=/opt/tiny-voca/phonemizer \
        /opt/tts/bin/python sounds/make_clips.py --voice F2

Output: sounds/<name>.wav, 16 kHz mono 16-bit, silence trimmed to 30 ms each
side. Offline fallback with the Windows voice: make_clips.ps1.
"""
import argparse
import os
import subprocess
import tempfile

import numpy as np
import onnxruntime as ort
import soundfile as sf

# Spoken text per clip. US spellings where the phonemizer needs them
# ("meters" sounds the same as "metres").
CLIPS = {
    "num_0": "Zero.", "num_1": "One.", "num_2": "Two.", "num_3": "Three.", "num_4": "Four.",
    "num_5": "Five.", "num_6": "Six.", "num_7": "Seven.", "num_8": "Eight.", "num_9": "Nine.",
    "metre": "meter.", "metres": "meters.",
    "ahead": "ahead.", "left": "left.", "right": "right.", "up": "up.", "down": "down.",
    "about": "About", "a_little": "a little", "you_are_back": "You are back.",
    "lost_target": "I lost the target.",
    "stopping": "Stopping.",
    "not_seen": "I have not seen that.",
    "did_not_catch": "I did not catch that.",
    "cannot_help": "I cannot help with that.",
    "cannot_retrace": "I cannot retrace without a path.",
    "name_keys": "Keys.",
    "name_keychain": "Keychain.",
    "name_cup": "Cup.",
    "name_mug": "Mug.",
    "name_bottle": "Bottle.",
    "name_phone": "Phone.",
}

TRIM = (
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
    "adelay=30,apad=pad_dur=0.03"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", choices=["F2", "M2"], default="F2")
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--model", default="/opt/tiny-voca/onnx/model.onnx")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    import dizione  # reads DIZIONE_DATA

    session = ort.InferenceSession(args.model)
    one = lambda v: np.array([v], dtype=np.float32)  # noqa: E731
    voice_id = 0 if args.voice == "F2" else 1
    os.makedirs(args.out, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        for name, text in CLIPS.items():
            # tiny-voca needs an end mark or the last word breaks off; the
            # mid-sentence words ("About", "a little") get one for synthesis.
            say = text if text[-1] in ".!?" else text + "."
            phones = dizione.phonemize(say)
            audio, _ = session.run(None, {
                "tokens": np.array([phones.ids], dtype=np.int64),
                "stress": np.array([phones.stress], dtype=np.int64),
                "voice": np.array([voice_id], dtype=np.int64),
                "speed": one(args.speed),
                "pitch_shift": one(0.0),
                "pitch_range": one(1.0),
            })
            audio = audio[0]
            audio = audio * min(1.0, 0.99 / max(1e-6, float(np.abs(audio).max())))
            raw = os.path.join(tmp, name + ".wav")
            sf.write(raw, audio, 24000)
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", TRIM,
                 "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
                 os.path.join(args.out, name + ".wav")],
                check=True,
            )
            print(f"{name + '.wav':18s} {text}")
    print(f"Made {len(CLIPS)} clips with tiny-voca {args.voice} in {args.out}")


if __name__ == "__main__":
    main()
