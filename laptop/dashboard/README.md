# dashboard

Owner: Zain. Vite + React + three.js (react-three-fiber), UI built with [animate-ui](https://animate-ui.com) primitives. World-frame dot map: named objects at `xyz_world`, wearer at camera pose, optional crumb trail, fingertip-to-target line. Optional live JPEG from `telemd` (team monitoring, local network only), spoken cue as a caption, mode banner (LIVE / HOLD / LOST), process health, timing panel. Reads the `bridge` WebSocket. Never on the wearer's path. JSON markers are enough if JPEG is off. Design: [`docs/nathans-revision.md`](../../docs/nathans-revision.md).

## Run (no Pi needed)

Two terminals:

```sh
cd laptop/bridge && npm install && npm run replay:dev   # loops ../samples/dev-reach.jsonl
cd laptop/dashboard && npm install && npm run dev       # open http://localhost:5173
```

`npm run replay` in `laptop/bridge` shows the single static sample instead, and `npm start` there takes live telemetry from the Pi. The dashboard reconnects on its own when the bridge restarts. It shows "No data" when no world state has arrived for 1 s, so a frozen screen never looks live.

## Layout

The 3D view fills the window. A floating top bar holds the LIVE / HOLD / LOST switch, the law, the intent and the feed status; the caption and the replay scrubber float along the bottom. Two panels slide in from the sides:

- **Guidance** (left): the bound target and the hand-to-target distance, what the wearer hears (law, reach ticks, pan, last phrase), and the session map.
- **System** (right): process heartbeats, the events timeline, timing, the camera preview, and the animations switch.

| Key | Does |
| --- | --- |
| `[` | Show or hide Guidance |
| `]` | Show or hide System |
| `Ctrl` / `Cmd` + `B` | Focus the 3D view (hide both), then bring back the panels that were open |

On a wide window an open panel pushes the 3D view aside; below 900 px it covers the view, one panel at a time. The browser remembers which panels were open.

Animations follow the system's reduced-motion setting. The switch under System, Display, turns them on or off for this browser only.

Look: palette, type and corner radius were dealt by the `design-taste-frontend` skill (graphite and orange, IBM Plex Sans and Mono, sharp). The orange marks the brand and the one primary action; LIVE / HOLD / LOST keep their own green, amber and red. The fonts are bundled (`@fontsource`), so the dashboard needs no internet, which matters on the Pi's phone hotspot.

## What is where

| File | What |
| --- | --- |
| `src/useTelemetry.js` | WebSocket to the bridge (`ws://127.0.0.1:8765`): latest world state, latest JPEG, staleness |
| `src/Scene.jsx` | World-frame dot map. Objects use `xyz_world`; the wearer uses `pose.T_world_from_cam`, or sits at the origin when telemetry has no `pose` (today's `telemd`; before odometry the world frame is the camera frame). `xyz_cam` is not drawn. Camera FOV is a display guess, not telemetry. |
| `src/worldScene.js` | Pure coordinate helpers: OpenCV world to three.js, pose translation/matrix, object/hand/crumb extraction. |
| `src/App.jsx` | Layout, shortcuts and the panels' contents. Top bar (animate-ui `Highlight` slides to the current mode, `RollingText` for law, intent and captions), live values (`SlidingNumber`), waiting state (`ShimmeringText`), animations switch (`Switch`) |
| `src/Sidebar.jsx` | One side panel on the animate-ui `sidebar` primitive: `Gap` reserves its width so the 3D view widens as it closes, `Container` slides it and its handle, `TriggerIcon` swaps the handle's icon |
| `src/Tip.jsx`, `src/icons.jsx` | animate-ui `Tooltip` with the control's shortcut; the inline stroke icons |
| `src/Scrubber.jsx` | Replay scrubber (animate-ui `Slider` and `Button`) over the last 10 min of world states |
| `src/clips.js` | Caption text for guided's clip ids, in `enum beacon_clip` order. `npm test` fails if the enum in `include/beacon.h` changes. |
| `src/events.js`, `src/Events.jsx` | Events timeline: process kills and restarts (with downtime) and LIVE / HOLD / LOST changes, from the history. Click one to scrub there; an animate-ui `Highlight` glides behind the row under the pointer. |

The 3D view draws the bound `target` even when `objects[]` is missing, as in `telemd`'s target-only messages.

## Replay scrubber

The dashboard keeps the last 10 minutes of world states, live or replayed, and keeps them across bridge restarts. Drag the slider, use the arrow buttons, or focus the slider and use the arrow keys to freeze the view on any past message. The top bar then shows Paused, and the label gives the time back plus the Pi's clock (`Pi t`) for matching QNX traces. Dragging to the end, End, or Go live returns to live. Video is not kept in history, so the camera panel hides while paused.

Breadcrumbs are drawn as small grey dots when `crumbs[]` is present. Boxes drawn on the video are not built yet.
