# Demo runbook: Best Use of QNX

Written for the Sunday demo and the 30-second Devpost video. Same beats for both: one recorded pass doubles as the video, and the live table demo repeats the same beats with judges watching.

Two passes, floor first:

- **Floor pass** (tonight, insurance): the two replay-clip scripts. Everything in them is already measured and in the bring-up log. Record it as soon as the room is quiet, and the Devpost video exists no matter what happens to the live camera.
- **Live pass** (after the end-to-end chain is stable): `device_live_demo.sh` from the C270, plus the kill beats. Record this one instead if it holds together, and perform it live at the table.

Source of truth for claims: `docs/qnx-prize-track.md`. If this runbook disagrees with the bring-up log (`docs/pi-bringup.md`) on what has been measured, the log wins.

## The 30 seconds

The camera (phone on a tripod) sees the table, the JBL Go 3, and the wearer's hand. The SSH terminal is visible on the laptop screen behind. The JBL must be audible in the recording; everything else is optional.

| Time | What happens | Say | Earns |
| --- | --- | --- | --- |
| 0 to 8 | FIND arrives (as a record, on the laptop). Spoken bearing from the JBL. | "It homes to a named item seen this session, on the Pi. The sound never waits on the model." | S7, S8 |
| 8 to 16 | Wearer walks toward the object; the cue repeats from sensors. | "Direction comes from the camera, and the audio thread runs on core 0 at FIFO 58. No model runs there." | S2, S6 |
| 16 to 24 | `slay` the perception producer. Cue holds, then "I lost the target." No distance spoken. | "The AI is dead. The guidance process is not, and it refuses to guess." | S1, S4 |
| 24 to 30 | Supervisor respawns the dead producer; the cue returns. Then kill the BT audio service, it comes back on its own. | "Components restart without a reboot. The thing that can fail cannot take the thing that must not with it." | S1, S6 |

Do not open with "60 Hz" or a tick rate. The S2 answer a QNX engineer wants is: audio never blocks on inference, the cue never lies, dead components restart without a reboot. The 16.67 ms number is supporting evidence, and it appears in the readout, not the pitch.

Reach ticks (hand enters, ticks speed up, tone) stay in the script only if MediaPipe hands come up on the device. As of the last log row they do not, and the spec's own fallback for that case is WALK speech only. Do not gesture a fake grab to imply the tone fired from hand tracking.

Say once, early (the spec's paragraph, shortened): "Beacon is a supplement to the cane, not a replacement. It does not detect stairs, obstacles or traffic. Sighted team, not yet tested with BLV wearers."

## Floor pass, on the Pi

Both scripts clean up after themselves and print the deadline readout at the end. Metres are on by default in the scripts; see "Metres" below before recording.

The target must be a word in the six-noun bake (`models/labels.txt`: bottle, can, keys, phone, box, mouse). The old `cup` scripts from the 32-noun era cannot bind. On the Nov 22 clips the strongest detection is the box at conf 0.14; the bottle sits at 0.06, so the scripts default `CONF` to 0.05. If the WALK cue never comes with `bottle`, re-run with `box`.

```
sh ingest/tools/device_chain_demo.sh /tmp/replay.avi bottle
```

Expected: guided speaks the WALK cue three times, mode goes LIVE then HOLD, and the STAT line at the end reads 1500 loops, 0 missed deadlines, worst lateness 4.7 ms, p95 1.9 ms.

```
sh ingest/tools/device_slay_beat.sh /tmp/long.avi bottle
```

Expected, in order:

- A: cue is live.
- B: `slay ingest`. Guidance keeps its record (1800 loops, 0 missed) and says "I lost the target."
- C: the readout after the producer died.
- D: a fresh `ingest` restores the cue with guided never restarted (2100 loops, 0 missed, p95 2.05 ms).

These two recordings are the floor video. If the live pass never stabilizes, submit this and the demo table performs the same scripts live.

## Live pass, from the C270

One-time setup, already solved once (log rows 2026-11-22 ~01:30): the sensor service needs `default_video_format = jpeg`, `create_window = false`, `memory_allocator_type = from_sensor` on the `usb_camera` unit. The script starts the service itself:

```
sh ingest/tools/device_live_demo.sh bottle 10.80.55.91
```

Perception must be warm before the FIND. The script enforces the order; if you start parts by hand, wait for the "records so far" count before the intent.

The kill beat (this is A5, not yet rehearsed, rehearse it twice before judging):

```
slay -f $(pidin ar | grep live_probe | awk '{print $1}')
```

Expected: guided goes HOLD then LOST and its deadline record continues unbroken. Say the process name out loud: "That was the perception process." If live perception is flaky at demo time, fall back to the floor-pass `slay ingest` beat, and say "the relay" instead.

The supervisor beat (verified, but not yet in the same take as the live loop):

```
supervisor --beacon        # starts guided and ingest with scheduler attributes
kill -9 <guided pid>
```

Expected: `guided fault (no output channel)` in the log, then a respawn in about 100 ms with 100/500/2000/5000 ms backoff. The supervisor also restarts a dead ingest child.

The restart-without-a-reboot beat (A2, rehearse once): `slay` the BT audio service process, and the service script brings the speaker back. This replaces the piezo beat, which was cancelled for lack of hardware.

Readback for judges, before or after the run:

```
uname -a
pidin ar
```

`pidin ar` shows `58f` for guided, `40f` for its audio thread, `22r` for ingest, `last_cpu=0` for guided and `1` for ingest. The ingest log line "runmask 0x2 applied (kernel said it was 0xf)" is the kernel's own readback; use it, because the runmask column renders empty on this image. Capture the `pidin ar` output with ORT live into `docs/pi-bringup.md` (A3) so the slide can quote it.

## Metres

All three device scripts pass `--metres`, so guided speaks "about one metre ahead." The depth scale has not been tape-checked on this camera. The README and the Devpost text say the demo gives direction, not a number, so one of these must happen before recording:

1. Run the tape check (10 minutes, one time): object at a taped 1 m, then
   `tape_check.py --json /tmp/beacon-live.jsonl --tape-m 1.0 --name bottle`.
   If 1 m error is under 30 percent, metres may stay on, and the Devpost honesty block should be updated to say the tape check passed.
2. Or remove `--metres` from the three scripts for the demo, and the cue speaks bearing only.

Default to option 2 unless the tape check actually passes tonight.

## Failure plays

Things that have already broken once, with the fix that worked:

- USB stack dies (no `/dev/usb`, `usbd_connect` fails): `sudo -n sh /usr/etc/usb_start.sh`, then restart `sensor` and `beacon_grab`. No reboot needed; rehearse this line.
- C270 wedged after a USB crash, survives reboots because a reboot does not drop VBUS: power-cycle it, `sudo -n gpio-rp1 set 42 op pn dl`, wait about 5 s, then `set 42 a2 pn` / `set 43 a2 pu`. If io-usb-otg went down with it, run `usb_start.sh` first.
- Live perception too slow or missing frames: fall back to the replay clip scripts. Say "capture is the stand-in; everything after reading a frame runs on device."
- JBL silent: check the BT service (`bt_speaker.py` path) before judging, and keep the slay-restart beat in the pocket as the fix.
- Dashboard dies: irrelevant to the demo. Do not stop for it.

## Rehearsal schedule

1. Floor pass now: both scripts once each, phone recording. ~20 minutes including the metres decision.
2. Live pass when the chain is stable: `device_live_demo.sh`, then the A5 kill twice, then the supervisor beat once, then the BT service beat once. ~40 minutes.
3. Record the live pass as the video if it holds. Two clean takes maximum, then use the floor video and stop spending time.

## Still open before this runbook is fully true

| Item | Owner | Done when |
| --- | --- | --- |
| A3: `pidin ar` with ORT live, saved to the log | Nathan | the readback is in `docs/pi-bringup.md` |
| A5: live perception producer killed twice on hardware | Nathan | two clean HOLD to LOST transitions logged |
| A6: metres decision executed | Nathan | tape check logged, or `--metres` removed from the three scripts |
| Re-record the replay clips with a clear object at about 1 m | Nathan | a clip where the target clears conf 0.15 at default lighting |
| BT service kill/restart rehearsed once | Matt, Munadir | the speaker comes back on its own in a run |
| Floor video recorded | any | a take exists with the JBL audible |
