# Live Camera and 3D Work Summary

This note continues [`dashboard-redesign.md`](dashboard-redesign.md) and records the path from that redesign to the current live-camera and 3D work. It is intended as a handoff for the next session.

## Starting point: dashboard redesign

`docs/dashboard-redesign.md` described a laptop-only redesign on `zain/dashboard-redesign`: a full-window 3D scene, floating status and replay controls, a Guidance/System panel on the left, and a camera panel on the right. PR #28 merged that work into `main` at `2429b7c` after Nathan's dashboard mock-data PR #26 was already in `main`.

The redesign also changed the bridge so Live and Replay can be switched without restarting it. UDP 5005 receives Pi telemetry and JPEGs; the dashboard uses a local WebSocket. At that point the camera panel could show a single composite image, but the Pi's checkout and live camera loop still needed work.

## Live camera work

After PR #28 merged, work moved to `zain/live-camera-24fps`, based on the updated `main`.

- The Pi camera capture was set to request 30 fps. A separate `percept/tools/live_preview.py` sender transmits the newest camera JPEG independently from detection, with a 24 fps send cap.
- The detector already rendered a composite containing the RGB frame with green detection boxes and labels above a colorized depth map. The Pi run was changed to send that composite separately from the raw feed.
- The laptop's Wi-Fi address was `10.80.55.92`; the Pi was `10.80.55.25`.
- A first attempt used only the raw camera feed, so the dashboard had no boxes or depth image. The live probe's composite output fixed that while it was running.
- The demo script now waits for the perception process to finish, so the Pi shell does not immediately tear down its background processes. It defaults to the current laptop address.

## Three camera views on the dashboard

The right panel now shows three stacked views:

1. Raw camera feed, sent independently on UDP 5005.
2. Object-detection view, showing the upper half of the probe's composite.
3. Depth map, showing the lower half of the same composite.

The bridge keeps telemetry and raw JPEGs on UDP 5005 and listens for the slower detector composite on UDP 5007. It tags WebSocket JPEG frames with a channel byte so the dashboard can keep the feeds separate. Legacy replay JPEGs remain readable as composites. The camera image updates are isolated from the top-level telemetry render to avoid making the 3D scene rerender for every video frame.

The panel and separate bridge listener were running in Chrome during the last check. The dashboard showed **Pi via Wi-Fi** and all three views. The one short browser measurement saw about 13 raw-frame updates per second, so 24 fps has not been demonstrated. The capture and sender request up to 24 fps, but the current measured rate is lower. The camera was pointed at a shelf/desk scene with no bottle detections, so the detection view had no green boxes at that moment; the detector log reported `mode=LOST objects=0`.

The bridge reported no telemetry earlier because the old bridge process had no UDP 5007 listener, and the Pi processes had stopped. Restarting the bridge on this code and starting the full Pi demo restored packet and image flow. A later run was started for 600 seconds with the corrected demo script. The most recent process check showed capture, raw preview, live probe, ingest, guided, and telemd running; recheck before relying on that state.

## Branch and push state

- `origin/zain/live-camera-24fps` was pushed with commit `d9a9c4c` (`feat: split live camera and vision previews`).
- The follow-up commit `e231889` (`perf: isolate live camera frame updates`) was committed locally on that branch and was **not pushed**, per the later instruction to stop pushing that branch.
- The current branch is `zain/live-3d-camera-following`, created from the local `zain/live-camera-24fps` tip at `e231889`. It is a child branch and has not been pushed.
- The working tree has one in-progress change in `percept/tools/probe_frame.py`: an optional `want_vo` argument can include the same frame, depth output, affine, and calibration in an internal `_vo_input` field. It does not yet drive a pose or alter the running Pi process.

## 3D camera-following status

The dashboard's 3D scene already renders the live objects and camera pose that arrive through telemetry. The current live path, however, publishes an identity pose and uses camera-relative object coordinates as `xyz_world`. That can show detections relative to the camera, but it cannot keep the 3D scene anchored as the camera moves.

`percept/tools/vo_core.py` contains depth-backed visual-odometry logic, and `percept/tools/vo_probe.py` uses it with captured or prerecorded frames. There is no live VO integration in `live_probe.py` yet. The previous investigation found that correct motion tracking needs to run VO on the live frames and publish a valid `T_world_from_cam`, then transform detected points from camera coordinates into world coordinates before `ingest` and `telemd` send them to the dashboard.

The VO code has a chest-height correction option. No measured chest height was established in this conversation. Any first live trajectory would therefore need to be marked approximate, or the correction should remain disabled until that measurement is supplied. The raw feed can stay at its independent camera rate; 3D pose and object updates will be limited by the perception/VO processing rate, which is lower than 24 fps.

## Next steps

1. Continue only on `zain/live-3d-camera-following`; do not push more commits to `zain/live-camera-24fps`.
2. Complete the optional live VO integration in `live_probe.py`, using the existing depth result from the same frame as the object detections.
3. Publish pose validity and `T_world_from_cam`, transform visible `xyz_cam` points to world space, and keep the dashboard's 3D scene honest when VO loses tracking.
4. Avoid restarting or replacing the Pi camera run while the friend working on the camera part needs it. The last observed Pi run used the existing 600-second demo and may need to be checked before any deployment.
5. After the pose path is ready and the camera run can be coordinated, verify that the 3D frustum moves with the camera and objects remain in a stable world position. Separately measure the raw video rate; it was about 13 fps in the last short browser sample.

No tests were run for the three-view dashboard or the unfinished VO change in this session. The dashboard was inspected live in Chrome; the Pi's actual camera/depth composite and the three-card layout were visible.
