import { useEffect, useState } from 'react';

const BRIDGE_URL = 'ws://127.0.0.1:8765';
const STALE_MS = 1000; // no world state for this long -> NO DATA, never a frozen LIVE
const FRAME_STALE_MS = 2000; // JPEG turned off or stopped -> hide the last frame
const MAX_HISTORY = 6000; // world states kept for the scrubber: 10 min at 10 Hz
const TRIM = 600; // drop this many of the oldest at a time

// World-state history (newest last) and the latest camera frame from the bridge.
// Reconnects when the bridge restarts. History survives reconnects so you can scrub after a run.
export function useTelemetry() {
  const [log, setLog] = useState({ first: 0, items: [] }); // items[i] = { at, world }; first = index of items[0]
  const [frame, setFrame] = useState(null); // { url, at }
  const [connected, setConnected] = useState(false);
  const [now, setNow] = useState(() => performance.now());

  useEffect(() => {
    let ws;
    let retry;
    let frameUrl;
    let stopped = false;
    const connect = () => {
      ws = new WebSocket(BRIDGE_URL);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) retry = setTimeout(connect, 1000);
      };
      ws.onmessage = ({ data }) => {
        const at = performance.now();
        if (typeof data === 'string') {
          const item = { at, world: JSON.parse(data) }; // the bridge only forwards JSON objects
          setLog(({ first, items }) => {
            const next = [...items, item];
            return next.length > MAX_HISTORY ? { first: first + TRIM, items: next.slice(TRIM) } : { first, items: next };
          });
        } else {
          if (frameUrl) URL.revokeObjectURL(frameUrl);
          frameUrl = URL.createObjectURL(data);
          setFrame({ url: frameUrl, at });
        }
      };
    };
    connect();
    const clock = setInterval(() => setNow(performance.now()), 250);
    return () => {
      stopped = true;
      clearTimeout(retry);
      clearInterval(clock);
      ws.close();
      if (frameUrl) URL.revokeObjectURL(frameUrl);
    };
  }, []);

  const last = log.items.at(-1);
  return {
    log,
    world: last?.world ?? null,
    connected,
    stale: !last || now - last.at > STALE_MS,
    frameUrl: frame && now - frame.at < FRAME_STALE_MS ? frame.url : null,
  };
}
