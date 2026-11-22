// bridge: telemd UDP in, WebSocket out, JSONL recording of every live session.
// Wire format and usage: README.md and ../samples/README.md.
import dgram from 'node:dgram';
import fs from 'node:fs';
import path from 'node:path';
import { once } from 'node:events';
import WebSocket, { WebSocketServer } from 'ws';

const MAX_CLIENT_BUFFER = 1 << 20; // a stalled dashboard is skipped, not queued for (newest wins)

// A datagram or replay line -> the world-state object, or null if it is not a JSON object.
export function parseWorld(data) {
  try {
    const msg = JSON.parse(String(data));
    return msg !== null && typeof msg === 'object' && !Array.isArray(msg) ? msg : null;
  } catch {
    return null;
  }
}

// A replay file is one JSON object (like world.sample.json) or JSONL, one object per line.
export function loadReplay(file) {
  const text = fs.readFileSync(file, 'utf8');
  const whole = parseWorld(text);
  if (whole) return [whole];
  const lines = text.split('\n').filter((line) => line.trim());
  const msgs = lines.map((line) => parseWorld(line)).filter(Boolean);
  if (msgs.length < lines.length) console.warn(`bridge: skipped ${lines.length - msgs.length} bad line(s) in ${file}`);
  if (msgs.length === 0) throw new Error(`no world-state messages in ${file}`);
  return msgs;
}

// Replay pacing from the Pi's t_ns: the real gap up to 5 s, else 100 ms (~10 Hz).
export function gapMs(a, b) {
  const ms = (b.t_ns - a.t_ns) / 1e6;
  return ms > 0 ? Math.min(ms, 5000) : 100;
}

// Live (no replayFile): telemd datagrams on udpPort. Replay: loop replayFile. Both fan out on wsPort.
export async function startBridge({ wsPort, udpPort, recordDir, replayFile, framesDir }) {
  const replay = replayFile && loadReplay(replayFile);

  const wss = new WebSocketServer({
    host: '127.0.0.1',
    port: wsPort,
    // Only pages served from this laptop may read the feed (it can carry camera frames); other sites get 401.
    verifyClient: ({ origin }) => !origin || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin),
  });
  wss.on('connection', (ws) => ws.on('error', () => {})); // a bad dashboard frame must not kill the recording
  await once(wss, 'listening');
  const send = (data) => {
    for (const ws of wss.clients) {
      if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount < MAX_CLIENT_BUFFER) ws.send(data);
    }
  };
  const closeWs = () => {
    for (const ws of wss.clients) ws.terminate();
    wss.close();
  };

  if (replay) {
    let i = 0;
    let timer;
    // Offline replay: a composite preview JPEG per record (probe --frames-dir),
    // sent just before the world state it depicts.
    const frameFor = (index) => {
      if (!framesDir) return null;
      const file = path.join(framesDir, `${String(index).padStart(6, '0')}.jpg`);
      try {
        return fs.readFileSync(file);
      } catch {
        return null;
      }
    };
    const tick = () => {
      const next = (i + 1) % replay.length;
      const frame = frameFor(i);
      if (frame) send(frame);
      send(JSON.stringify(replay[i]));
      timer = setTimeout(tick, gapMs(replay[i], replay[next]));
      i = next;
    };
    tick();
    return { wsPort: wss.address().port, close: () => { clearTimeout(timer); closeWs(); } };
  }

  fs.mkdirSync(recordDir, { recursive: true });
  const file = path.join(recordDir, `${new Date().toISOString().replace(/[:.]/g, '-')}.jsonl`);
  const stats = { world: 0, video: 0, dropped: 0 };
  const udp = dgram.createSocket('udp4');
  udp.on('message', (buf) => {
    if (buf[0] === 0xff && buf[1] === 0xd8) { // JPEG start-of-image marker
      stats.video++;
      send(buf);
      return;
    }
    const msg = parseWorld(buf);
    if (!msg) {
      stats.dropped++;
      return;
    }
    const line = JSON.stringify(msg); // one line even if telemd pretty-prints
    fs.appendFileSync(file, line + '\n'); // sync, so Ctrl+C or a crash never loses a buffered line
    stats.world++;
    send(line);
  });
  udp.bind(udpPort);
  await once(udp, 'listening');

  const status = setInterval(() => {
    console.log(`bridge: last 5 s: ${stats.world} world, ${stats.video} video, ${stats.dropped} dropped, ${wss.clients.size} dashboard(s)`);
    stats.world = stats.video = stats.dropped = 0;
  }, 5000);

  return {
    wsPort: wss.address().port,
    udpPort: udp.address().port,
    file,
    close: () => { clearInterval(status); udp.close(); closeWs(); },
  };
}
