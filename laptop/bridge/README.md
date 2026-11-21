# bridge

Owner: Zain. Node 20+. UDP in from `telemd`, WebSocket out to the dashboard, records every session to JSONL for replay. Never on the wearer's path. Message format: [`../samples/`](../samples/). Design: [`docs/nathans-revision.md`](../../docs/nathans-revision.md) §3 (remote monitor).

## Run

```sh
npm install
npm start                    # live: telemd -> UDP 5005 on this laptop -> ws://127.0.0.1:8765
npm run replay:dev           # loop ../samples/dev-reach.jsonl: walk, reach, slay percept -> HOLD -> LOST (no Pi needed)
npm run replay               # loop the single static ../samples/world.sample.json
node main.js <file.jsonl>    # loop any recording or replay file
npm test
```

- Live mode prints a status line every 5 s (world, video, dropped, dashboards). `0 world` means `telemd` is not reaching this laptop. Check that the laptop is on the same network as the Pi (see [`docs/pi-dev-workflow.md`](../../docs/pi-dev-workflow.md)), the IP `telemd` sends to (`ipconfig` on this laptop), and the firewall.
- Windows firewall: Windows marks a newly joined phone hotspot as a Public network. Set it to Private, or allow Node on public networks when Windows asks on the first run. Otherwise UDP from the Pi never arrives.
- Recordings go to `recordings/<UTC time>.jsonl` (gitignored), one world-state object per line, created on the first message. Video is forwarded live but never written to disk.
- Video is optional. With the JPEG off in `telemd`, the dashboard still gets every world-state message.
- Replay loops the file, paced by each message's `t_ns` (real gaps up to 5 s, 100 ms when there is no usable gap). The dashboard keeps its own history for the scrubber; the bridge only streams.

## Wire format

| Direction | Where | One message is |
| --- | --- | --- |
| In from `telemd` | UDP port 5005, all interfaces (local network only, never cloud) | One datagram: a world-state JSON object, or one JPEG (starts `FF D8`, under 60 KB). Anything else is dropped and counted. |
| Out to dashboards | `ws://127.0.0.1:8765` (this laptop only; browser pages must come from `localhost` or `127.0.0.1`, other sites get 401) | Text frame: world-state JSON on one line, as recorded. Binary frame: one JPEG. |

The bridge checks only that a message is a JSON object, not its fields. A dashboard more than 1 MB behind is skipped until it catches up (newest wins, nothing queues).
