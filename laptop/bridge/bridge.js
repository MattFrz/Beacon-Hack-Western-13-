// bridge: telemd UDP in, WebSocket out, JSONL recording of every live session.
// Wire format and usage: README.md and ../samples/README.md.
import dgram from 'node:dgram';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import WebSocket, { WebSocketServer } from 'ws';

const MAX_CLIENT_BUFFER = 1 << 20; // a stalled dashboard is skipped, not queued for (newest wins)
const STATUS_MS = 1000; // how often dashboards hear the source and how long ago the Pi last sent

const isV4 = (a) => a.family === 'IPv4' || a.family === 4; // Node 18 reports the number 4
const v4Int = (ip) => ip.split('.').reduce((n, part) => (n << 8) | Number(part), 0);

// The laptop's network adapter on the same subnet as a sender ("Wi-Fi", "Ethernet", "wlan0"), so the
// dashboard can say how the Pi reaches it. Loopback is a simulator on this laptop; null if no adapter matches.
export function adapterFor(address, interfaces = os.networkInterfaces()) {
  if (address.startsWith('127.')) return 'this laptop';
  for (const [name, addrs] of Object.entries(interfaces)) {
    for (const a of addrs ?? []) {
      if (isV4(a) && !a.internal && (v4Int(a.address) & v4Int(a.netmask)) === (v4Int(address) & v4Int(a.netmask))) return name;
    }
  }
  return null;
}

// This laptop's IPv4 addresses, for the destination telemd sends to.
export function laptopAddresses(interfaces = os.networkInterfaces()) {
  return Object.entries(interfaces).flatMap(([name, addrs]) =>
    (addrs ?? []).filter((a) => isV4(a) && !a.internal).map((a) => ({ address: a.address, adapter: name })),
  );
}

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

// Two sources, switchable while running: 'live' forwards telemd datagrams from udpPort, 'replay' loops
// replayFile. Both fan out on wsPort. UDP is always open, so live sessions are recorded (when recordDir is
// set) whichever source dashboards are watching. A dashboard switches by sending {"source": "live"} or
// {"source": "replay"}; nothing else it sends is acted on.
export async function startBridge({ wsPort, udpPort = 0, recordDir, replayFile, framesDir, source, recordings = [] }) {
  const entries = recordings.map((entry) => ({ ...entry, records: loadReplay(entry.file) }));
  let replay = entries.find(entry => entry.file === replayFile) ?? entries[0];
  if (replayFile && !entries.some(entry => entry.file === replayFile)) {
    const id = path.basename(replayFile).replace(/\.jsonl?$/, '');
    replay = { id, label: id, framesDir, records: loadReplay(replayFile) };
    entries.push(replay);
  }
  let current = source ?? (replay ? 'replay' : 'live');

  const wss = new WebSocketServer({
    host: '127.0.0.1',
    port: wsPort,
    // Only pages served from this laptop may read the feed (it can carry camera frames); other sites get 401.
    verifyClient: ({ origin }) => !origin || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin),
  });
  await once(wss, 'listening');
  const sendTo = (ws, data) => {
    if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount < MAX_CLIENT_BUFFER) ws.send(data);
  };
  const send = (data) => {
    for (const ws of wss.clients) sendTo(ws, data);
  };
  const closeWs = () => {
    for (const ws of wss.clients) ws.terminate();
    wss.close();
  };

  // Replay: a composite preview JPEG per record (probe --frames-dir), sent just before the world state it depicts.
  let i = 0;
  let timer;
  const frameFor = (index) => {
    if (!replay.framesDir) return null;
    try {
      return fs.readFileSync(path.join(replay.framesDir, `${String(index).padStart(6, '0')}.jpg`));
    } catch {
      return null;
    }
  };
  const tick = () => {
    const records = replay.records;
    const next = (i + 1) % records.length;
    const frame = frameFor(i);
    if (frame) send(frame);
    send(JSON.stringify(records[i]));
    timer = setTimeout(tick, gapMs(records[i], records[next]));
    i = next;
  };

  // Live: the last sender is the Pi (or a simulator on this laptop); dashboards are told its address and adapter.
  let pi = null; // { address, adapter, at }
  let file = null;
  if (recordDir) {
    fs.mkdirSync(recordDir, { recursive: true });
    file = path.join(recordDir, `${new Date().toISOString().replace(/[:.]/g, '-')}.jsonl`);
  }
  const stats = { world: 0, video: 0, dropped: 0 };
  const udp = dgram.createSocket('udp4');
  udp.on('message', (buf, rinfo) => {
    const jpeg = buf[0] === 0xff && buf[1] === 0xd8;
    const msg = jpeg ? null : parseWorld(buf);
    if (!jpeg && (!msg || !Number.isFinite(msg.t_ns))) {
      stats.dropped++;
      return;
    }
    const fresh = !pi || pi.address !== rinfo.address;
    pi = { address: rinfo.address, adapter: fresh ? adapterFor(rinfo.address) : pi.adapter, at: Date.now() };
    if (fresh) sendStatus();
    if (jpeg) {
      stats.video++;
      if (current === 'live') send(buf);
      return;
    }
    const line = JSON.stringify(msg); // one line even if telemd pretty-prints
    if (file) fs.appendFileSync(file, line + '\n'); // sync, so Ctrl+C or a crash never loses a buffered line
    stats.world++;
    if (current === 'live') send(line);
  });
  udp.bind(udpPort);
  await once(udp, 'listening');

  // What dashboards show about the feed. World states never carry a top-level "bridge" key.
  const status = () =>
    JSON.stringify({
      bridge: {
        source: current,
        replay: replay?.id ?? null,
        recordings: entries.map(({ id, label, framesDir }) => ({ id, label, video: Boolean(framesDir) })),
        pi: pi && { address: pi.address, adapter: pi.adapter, age_ms: Date.now() - pi.at },
        listen: { port: udp.address().port, addresses: laptopAddresses() },
      },
    });
  function sendStatus() {
    send(status());
  }

  const setSource = (next, id) => {
    const selected = next === 'replay' && id !== undefined ? entries.find(entry => entry.id === id) : replay;
    if ((next === 'replay' && !selected) || (next === current && selected === replay)) return;
    replay = selected;
    current = next;
    clearTimeout(timer);
    i = 0;
    sendStatus();
    if (current === 'replay') tick();
  };
  wss.on('connection', (ws) => {
    ws.on('error', () => {}); // a bad dashboard frame must not kill the recording
    ws.on('message', (data, isBinary) => {
      const msg = isBinary ? null : parseWorld(data);
      if (msg?.source === 'live' || msg?.source === 'replay') setSource(msg.source, msg.replay);
    });
    sendTo(ws, status());
  });

  if (current === 'replay') tick();
  let beats = 0;
  const heartbeat = setInterval(() => {
    sendStatus();
    if (++beats % 5) return;
    console.log(`bridge: last 5 s (${current}): ${stats.world} world, ${stats.video} video, ${stats.dropped} dropped, ${wss.clients.size} dashboard(s)`);
    stats.world = stats.video = stats.dropped = 0;
  }, STATUS_MS);

  return {
    wsPort: wss.address().port,
    udpPort: udp.address().port,
    file,
    close: () => { clearTimeout(timer); clearInterval(heartbeat); udp.close(); closeWs(); },
  };
}
