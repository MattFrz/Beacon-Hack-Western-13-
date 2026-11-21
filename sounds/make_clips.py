"""Make every Beacon voice clip with an offline text-to-speech model.

Runs once on a laptop (Linux / WSL); Beacon only plays the finished WAVs.
Both engines are Apache-2.0 and run locally on CPU.

Default: Inflect Mini v3, voice "hope" (https://huggingface.co/owensong/Inflect-Mini-v3)
    python3 -m venv /opt/tts && /opt/tts/bin/pip install numpy soundfile onnxruntime uv
    /opt/tts/bin/uv python install 3.12 && /opt/tts/bin/uv venv -p 3.12 /opt/inflect-venv
    /opt/tts/bin/uv pip install -p /opt/inflect-venv/bin/python huggingface-hub==0.36.2
    /opt/inflect-venv/bin/hf download owensong/Inflect-Mini-v3 --local-dir /opt/inflect-mini-v3
    cd /opt/inflect-mini-v3 && /opt/inflect-venv/bin/python verify_release.py
    /opt/tts/bin/uv pip install -p /opt/inflect-venv/bin/python -r core/requirements-cpu.txt
    sudo apt install ffmpeg
    /opt/tts/bin/python sounds/make_clips.py                     # ~6 min for 32 clips

Alternative: tiny-voca, voice F2 (https://huggingface.co/n4ze3m/tiny-voca)
    /opt/tts/bin/pip install huggingface_hub git+https://github.com/n4ze3m/dizione
    /opt/tts/bin/hf download n4ze3m/tiny-voca onnx/model.onnx config.json \
        --include "phonemizer/*" --local-dir /opt/tiny-voca
    DIZIONE_DATA=/opt/tiny-voca/phonemizer \
        /opt/tts/bin/python sounds/make_clips.py --engine tinyvoca --voice F2

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

# Whole phrases, so a walk cue is 3 joins ("Keys." + "About two meters." +
# "A little left.") instead of 6 single words, and sounds like one sentence.
# The player should prefer these over the single-word clips when it can.
_NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
for _n in range(1, 10):
    CLIPS[f"about_{_n}_metre" + ("" if _n == 1 else "s")] = (
        f"About {_NUM_WORDS[_n]} meter{'' if _n == 1 else 's'}.")
CLIPS["a_little_left"] = "A little left."
CLIPS["a_little_right"] = "A little right."
# Target out of view, bearing from the session map (spec §7 Range 3).
CLIPS["turn_left"] = "Turn left."
CLIPS["turn_right"] = "Turn right."
# Hand has stayed on the target: confirm, then stop the tone.
CLIPS["found_it"] = "Found it."

TRIM = (
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
    "adelay=10,apad=pad_dur=0.01"
)


def to_clip(raw: str, out_wav: str) -> None:
    """Resample to 16 kHz mono 16-bit and trim silence to 10 ms each side."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", TRIM,
         "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", out_wav],
        check=True,
    )


def make_inflect(args) -> None:
    """Inflect Mini v3 (owensong/Inflect-Mini-v3, Apache-2.0), run through its
    own launcher once per clip. About 11 s per clip on a laptop CPU."""
    voice = args.voice or "hope"
    only = set(args.only.split(",")) if args.only else None
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in CLIPS.items():
            if only and name not in only:
                continue
            say = text if text[-1] in ".!?" else text + "."
            raw = os.path.join(tmp, name + ".wav")
            subprocess.run(
                [args.inflect_python, "run.py", "speech", "--voice", voice,
                 "--text", say, "--subtype", "PCM_16", "--output", raw],
                cwd=args.inflect_dir, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            to_clip(raw, os.path.join(args.out, name + ".wav"))
            print(f"{name + '.wav':18s} {text}", flush=True)
    print(f"Made {len(only) if only else len(CLIPS)} clips with Inflect Mini v3 ({voice}) in {args.out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["inflect", "tinyvoca"], default="inflect")
    ap.add_argument("--voice", default=None,
                    help="inflect: cassidy|mark|hope|james|sophia|jasper (default hope); "
                         "tinyvoca: F2|M2 (default F2)")
    ap.add_argument("--speed", type=float, default=1.05, help="tinyvoca only")
    ap.add_argument("--model", default="/opt/tiny-voca/onnx/model.onnx", help="tinyvoca only")
    ap.add_argument("--inflect-dir", default="/opt/inflect-mini-v3")
    ap.add_argument("--inflect-python", default="/opt/inflect-venv/bin/python")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--only", default="", help="comma-separated clip names (inflect)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    if args.engine == "inflect":
        make_inflect(args)
        return

    import dizione  # reads DIZIONE_DATA

    args.voice = args.voice or "F2"

    session = ort.InferenceSession(args.model)
    one = lambda v: np.array([v], dtype=np.float32)  # noqa: E731
    voice_id = 0 if args.voice == "F2" else 1

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
            to_clip(raw, os.path.join(args.out, name + ".wav"))
            print(f"{name + '.wav':18s} {text}")
    print(f"Made {len(CLIPS)} clips with tiny-voca {args.voice} in {args.out}")


if __name__ == "__main__":
    main()
