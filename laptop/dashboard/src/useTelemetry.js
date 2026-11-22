import { useCallback, useEffect, useRef, useState } from 'react';

const BRIDGE_URL = 'ws://127.0.0.1:8765';
const STALE_MS = 1000; // no world state for this long -> NO DATA, never a frozen LIVE
const FRAME_STALE_MS = 2000; // JPEG turned off or stopped -> hide the last frame
const MAX_HISTORY = 6000; // world states kept for the scrubber: 10 min at 10 Hz
const TRIM = 600; // drop this many of the oldest at a time
const EMPTY = { first: 0, items: [] };

// World-state history (newest last), the latest camera frame, and the bridge's own status (which source it
// plays, and the last Pi it heard). Reconnects when the bridge restarts; history survives reconnects so you
// can scrub after a run, but starts over when the source changes, so replay and live never share a timeline.
export function useTelemetry() {
  const [log, setLog] = useState(EMPTY); // items[i] = { at, world }; first = index of items[0]
  const [frame, setFrame] = useState(null); // { url, at }
  const [bridge, setBridge] = useState(null); // { source, replay, pi, listen } from the bridge, every second
  const [connected, setConnected] = useState(false);
  const [now, setNow] = useState(() => performance.now());
  const wsRef = useRef(null);

  useEffect(() => {
    let ws;
    let retry;
    let frameUrl;
    let source; // the source the history belongs to
    let stopped = false;
    const connect = () => {
      ws = wsRef.current = new WebSocket(BRIDGE_URL);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) retry = setTimeout(connect, 1000);
      };
      ws.onmessage = ({ data }) => {
        const at = performance.now();
        if (typeof data !== 'string') {
          if (frameUrl) URL.revokeObjectURL(frameUrl);
          frameUrl = URL.createObjectURL(data);
          setFrame({ url: frameUrl, at });
          return;
        }
        const msg = JSON.parse(data); // the bridge only sends JSON objects
        if (msg.bridge) {
          if (source !== undefined && msg.bridge.source !== source) {
            setLog(EMPTY);
            setFrame(null);
          }
          source = msg.bridge.source;
          setBridge(msg.bridge);
          return;
        }
        setLog(({ first, items }) => {
          const next = [...items, { at, world: msg }];
          return next.length > MAX_HISTORY ? { first: first + TRIM, items: next.slice(TRIM) } : { first, items: next };
        });
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

  // Ask the bridge to play 'live' (the Pi) or 'replay' (its recording); it answers with a status message.
  const setSource = useCallback((next) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({ source: next }));
  }, []);

  const last = log.items.at(-1);
  return {
    log,
    world: last?.world ?? null,
    bridge: connected ? bridge : null,
    setSource,
    connected,
    stale: !last || now - last.at > STALE_MS,
    frameUrl: frame && now - frame.at < FRAME_STALE_MS ? frame.url : null,
  };
}
