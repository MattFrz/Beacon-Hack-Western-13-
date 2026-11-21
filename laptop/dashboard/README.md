# dashboard

Owner: Zain. Vite + React + three.js (react-three-fiber), UI built with [animate-ui](https://animate-ui.com) primitives. Torso and chest camera cone, optional live JPEG from `telemd` (team monitoring, local network only), objects at their 3D positions, fingertip-to-target line, spoken cue as a caption, mode banner (LIVE / HOLD / LOST), process health, timing panel. Reads the `bridge` WebSocket. Never on the wearer's path. JSON markers are enough if JPEG is off. Design: [`docs/nathans-revision.md`](../../docs/nathans-revision.md).

## Run (no Pi needed)

Two terminals:

```sh
cd laptop/bridge && npm install && npm run replay:dev   # loops ../samples/dev-reach.jsonl
cd laptop/dashboard && npm install && npm run dev       # open http://localhost:5173
```

`npm run replay` in `laptop/bridge` shows the single static sample instead, and `npm start` there takes live telemetry from the Pi. The dashboard reconnects on its own when the bridge restarts. It shows NO DATA when no world state has arrived for 1 s, so a frozen screen never looks LIVE.

## What is where

| File | What |
| --- | --- |
| `src/useTelemetry.js` | WebSocket to the bridge (`ws://127.0.0.1:8765`): latest world state, latest JPEG, staleness |
| `src/Scene.jsx` | 3D view. Everything is drawn in the camera frame, so `xyz_cam` goes in unchanged. Chest height, a 30° pitch and the Camera Module 3 FOV are display guesses, not telemetry. |
| `src/App.jsx` | Header (animate-ui `Highlight` slides to the current mode, `RollingText` for law, intent and spoken captions), side panels (`SlidingNumber` for live values) |
| `src/Scrubber.jsx` | Replay scrubber (animate-ui `Slider` and `Button`) over the last 10 min of world states |
| `src/clips.js` | Caption text for guided's clip ids, in `enum beacon_clip` order. `npm test` fails if the enum in `include/beacon.h` changes. |

The 3D view draws the bound `target` even when `objects[]` is missing, as in `telemd`'s target-only messages.

## Replay scrubber

The dashboard keeps the last 10 minutes of world states, live or replayed, and keeps them across bridge restarts. Drag the slider, use ◀ ▶, or focus the slider and use the arrow keys to freeze the view on any past message. The header then shows PAUSED, and the label gives the time back plus the Pi's clock (`Pi t`) for matching QNX traces. Dragging to the end, End, or Live returns to live. Video is not kept in history, so the camera panel hides while paused.

Not built yet: breadcrumbs, boxes drawn on the video.
