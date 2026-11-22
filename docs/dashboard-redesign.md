# Dashboard redesign and live Pi connection

Branch `zain/dashboard-redesign`, not yet a PR. Everything here is laptop-side (`laptop/dashboard`, `laptop/bridge`); nothing touches the wearer's path.

## What changed

**Layout.** The 3D view fills the window. A floating top bar holds the LIVE / HOLD / LOST switch, law, intent, the Live | Replay switch, the feed status and a full-screen button. The caption and replay scrubber float along the bottom. Two animated panels (animate-ui `sidebar` primitive) slide from the sides and the 3D view widens as they close.

- **Left, 320 px:** animate-ui tabs on React Aria. *Guidance*: target, hand distance, what the wearer hears, session map and remembered objects. *System*: Data source, process heartbeats, events timeline, timing, Animations switch. The last tab is remembered per browser.
- **Right, 440 px:** the camera frame at full width (Nathan's composite: image with detection boxes over the depth map).
- **Keys:** `[` left panel, `]` camera, `Ctrl/Cmd+B` hide both for full-screen 3D. Below 900 px a panel covers the view, one at a time.

**Look.** Dealt by the `design-taste-frontend` skill: graphite and orange, IBM Plex Sans and Mono (bundled with `@fontsource`, so no internet needed on the hotspot), sharp corners. Orange marks only the brand and the one primary button, so LIVE/HOLD/LOST keep their own green/amber/red.

**animate-ui used:** Sidebar, Tabs (React Aria), Button, Highlight (mode switch, source switch, events rows), Tooltip, RollingText, SlidingNumber, ShimmeringText, Switch, Slider. Animations follow the OS reduced-motion setting; System, Display has a switch to override it per browser.

**Nathan's mock data (PR #26).** `main` merged in. The camera panel shows his frames; Session map lists remembered objects (newest first, target tagged); pose shows "interpolated"; `targetObjectId` stops the target being drawn twice (guided numbers it, percept names `bottle-1`); fast-changing YOLO/depth times are plain text, not rolling digits.

## Live Raspberry Pi connection

The bridge used to pick its source at start-up. Now it switches while running.

- **Bridge (`bridge.js`, `main.js`):** UDP 5005 is always open and live sessions are always recorded. A dashboard sends `{"source":"live"|"replay"}` (nothing else is acted on). Once a second, and on every change, the bridge sends a status frame: source, replay name, last sender (address, laptop adapter, age) and this laptop's addresses. `npm start` starts live with the vid360 recording loaded; `replay:*` scripts start on their file.
- **Dashboard:** *Live | Replay* switch in the top bar. The status pill reads "Pi via Wi-Fi" (green) while packets are fresh (under 2 s), "Recording" for replay, "Waiting for the Pi" otherwise. While waiting, the view shows the `telemd` command with this laptop's addresses and a "Play the recording instead" button. History resets on each switch so replay and live never share a timeline.
- **Tested:** bridge 12/12, dashboard 18/18, build passes. Live path checked first with a script sending from the laptop's Wi-Fi address, then with real packets from the Pi.

### Running it against the Pi

1. Join the hotspot (`cybernet`, password from Nathan). Laptop got `10.80.55.92`; Pi is `10.80.55.25`.
2. Windows marks the hotspot Public; Node is already allowed through the firewall on Public. NordLynx (VPN) is also on this laptop, so pause it if packets do not arrive.
3. `cd laptop/bridge && npm start`, then `cd laptop/dashboard && npm run dev`.
4. SSH: `ssh beacon-pi` (key auth; `~/.ssh/config` pins `aes128-ctr` + `hmac-sha2-256` because Windows OpenSSH otherwise fails with "Corrupted MAC on input").
5. On the Pi, send `telemd` at the laptop: `/data/home/qnxuser/Beacon-Hack-Western-13-/telemd/build/telemd 10.80.55.92 5005`. It only reads `/beacon_world`, so something must write it (`guided`, `fakeworld` or `ingest`).

### What actually ran on the Pi

A simulated scenario: `fakeworld lost` + `guided` + `telemd`, 6 rounds of 16 s, started detached from `/tmp/pi_demo.sh` (logs in `/tmp/demo.log`, `/tmp/telemd.log`). The dashboard showed "Pi via Wi-Fi" from `10.80.55.25`. **No camera loop ran**: the Pi's checkout predates `main`, so `ingest/tools/device_live_demo.sh` is missing. Data is simulated; connection and dashboard are real.

## Still open

- Update the Pi's checkout (ask Nathan how he deploys), then run `sh ingest/tools/device_live_demo.sh <noun> 10.80.55.92 300` for real camera, detections and frames.
- **Ask Nathan before any run that stops processes:** that script slays running Beacon processes.
- Remove the laptop's key from the Pi when done: delete the `zain-laptop-beacon` line from `~/.ssh/authorized_keys`.
- A `[` / `]` press once flipped both panels during testing and never repeated; unexplained.
- Not rechecked at phone width after the camera-panel and source-switch changes.
- Opening the PR: `graphify graph updated` must pass (see Graph below), then merge `main` again first.

## Graph

Refreshed with graphify's code-only update (free). This file and the changed READMEs are docs, which only the full `/graphify . --update` skill run reads; run that once before the PR if you want them in the graph.
