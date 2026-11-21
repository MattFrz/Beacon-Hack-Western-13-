"""Make every Beacon voice clip with a natural neural voice.

Runs on Linux / WSL, needs internet once (Microsoft's free neural voices via
edge-tts) and ffmpeg:

    python3 -m venv /opt/tts && /opt/tts/bin/pip install edge-tts
    sudo apt install ffmpeg
    /opt/tts/bin/python sounds/make_clips.py

Output: sounds/<name>.wav, 16 kHz mono 16-bit, silence trimmed to 30 ms each
side. Offline fallback with the robotic Windows voice: make_clips.ps1.
"""
import asyncio
import os
import subprocess
import tempfile

import edge_tts

VOICE = "en-CA-ClaraNeural"  # Canadian English, says "metres" the way we spell it
RATE = "+15%"  # a full walk cue must fit inside the 3 s repeat

CLIPS = {
    "num_0": "zero", "num_1": "one", "num_2": "two", "num_3": "three", "num_4": "four",
    "num_5": "five", "num_6": "six", "num_7": "seven", "num_8": "eight", "num_9": "nine",
    "metre": "metre", "metres": "metres",
    "ahead": "ahead", "left": "left", "right": "right", "up": "up", "down": "down",
    "about": "about", "a_little": "a little", "you_are_back": "You are back.",
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


async def make(name: str, text: str, out_dir: str, tmp: str) -> None:
    mp3 = os.path.join(tmp, name + ".mp3")
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(mp3)
    wav = os.path.join(out_dir, name + ".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", TRIM,
         "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", wav],
        check=True,
    )
    print(f"{name + '.wav':18s} {text}")


async def main() -> None:
    out_dir = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in CLIPS.items():
            await make(name, text, out_dir, tmp)
    print(f"Made {len(CLIPS)} clips with {VOICE} in {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
