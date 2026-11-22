import { test } from 'node:test';
import assert from 'node:assert/strict';
import dgram from 'node:dgram';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';
import { parseWorld, loadReplay, gapMs, startBridge, adapterFor, laptopAddresses } from './bridge.js';

const sampleFile = fileURLToPath(new URL('../samples/world.sample.json', import.meta.url));
const tmpDir = () => fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-'));
const isStatus = (m) => typeof m === 'string' && m.startsWith('{"bridge":');

// The next n feed messages (status messages skipped): strings for text frames, Buffers for binary frames.
function collect(ws, n) {
  return new Promise((resolve, reject) => {
    const got = [];
    const timer = setTimeout(() => reject(new Error(`timed out with ${got.length}/${n} messages`)), 2000);
    ws.on('message', (data, isBinary) => {
      const m = isBinary ? data : data.toString();
      if (isStatus(m)) return;
      got.push(m);
      if (got.length === n) {
        clearTimeout(timer);
        resolve(got);
      }
    });
  });
}

// The next status message that passes the check.
function status(ws, check = () => true) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('no matching status message')), 2000);
    const onMessage = (data, isBinary) => {
      const m = isBinary ? null : data.toString();
      if (!isStatus(m)) return;
      const { bridge } = JSON.parse(m);
      if (!check(bridge)) return;
      clearTimeout(timer);
      ws.off('message', onMessage);
      resolve(bridge);
    };
    ws.on('message', onMessage);
  });
}

const fakeInterfaces = {
  'Wi-Fi': [{ family: 'IPv4', address: '10.80.55.12', netmask: '255.255.255.0', internal: false }],
  Ethernet: [{ family: 4, address: '192.168.1.20', netmask: '255.255.255.0', internal: false }],
  Loopback: [{ family: 'IPv4', address: '127.0.0.1', netmask: '255.0.0.0', internal: true }],
};

test('adapterFor names the laptop adapter on the sender subnet', () => {
  assert.equal(adapterFor('10.80.55.25', fakeInterfaces), 'Wi-Fi'); // the Pi on the phone hotspot
  assert.equal(adapterFor('192.168.1.7', fakeInterfaces), 'Ethernet');
  assert.equal(adapterFor('127.0.0.1', fakeInterfaces), 'this laptop');
  assert.equal(adapterFor('172.16.0.9', fakeInterfaces), null);
  assert.deepEqual(laptopAddresses(fakeInterfaces), [
    { address: '10.80.55.12', adapter: 'Wi-Fi' },
    { address: '192.168.1.20', adapter: 'Ethernet' },
  ]);
});

test('parseWorld keeps JSON objects only', () => {
  assert.deepEqual(parseWorld('{"v":1}'), { v: 1 });
  for (const bad of ['not json', '[1]', 'null', '3', '']) assert.equal(parseWorld(bad), null);
});

test('gapMs paces by t_ns, 100 ms when unusable, capped at 5 s', () => {
  assert.equal(gapMs({ t_ns: 0 }, { t_ns: 50e6 }), 50);
  assert.equal(gapMs({ t_ns: 50e6 }, { t_ns: 0 }), 100); // loop wrap
  assert.equal(gapMs({}, {}), 100);
  assert.equal(gapMs({ t_ns: 0 }, { t_ns: 60e9 }), 5000);
});

test('loadReplay reads the pretty sample or JSONL, skipping bad lines', () => {
  assert.equal(loadReplay(sampleFile).length, 1);
  const file = path.join(tmpDir(), 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0}\r\nbroken\n{"t_ns":1}\n');
  assert.deepEqual(loadReplay(file), [{ t_ns: 0 }, { t_ns: 1 }]);
});

test('live: forwards world JSON and JPEGs, drops junk, records world lines', async () => {
  const bridge = await startBridge({ wsPort: 0, udpPort: 0, recordDir: tmpDir() });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  await once(ws, 'open');
  const got = collect(ws, 2);

  const sample = fs.readFileSync(sampleFile, 'utf8'); // pretty-printed; must arrive as one line
  const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 1, 2, 3]);
  const udp = dgram.createSocket('udp4');
  for (const datagram of ['junk', '[1,2]', sample, jpeg]) udp.send(datagram, bridge.udpPort, '127.0.0.1');
  const msgs = await got;
  udp.close();
  ws.close();
  bridge.close();

  const line = JSON.stringify(JSON.parse(sample));
  assert.equal(msgs.find((m) => typeof m === 'string'), line); // junk would have arrived first
  // camera JPEGs on the main port go out tagged with channel 1 (raw camera); the preview port uses 2
  assert.deepEqual(msgs.find((m) => Buffer.isBuffer(m)), Buffer.concat([Buffer.from([1]), jpeg]));
  assert.equal(fs.readFileSync(bridge.file, 'utf8'), line + '\n');
});

test('rejects pages from other sites', async () => {
  const bridge = await startBridge({ wsPort: 0, replayFile: sampleFile });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`, { origin: 'https://example.com' });
  const [err] = await once(ws, 'error');
  bridge.close();

  assert.match(err.message, /401/);
});

test('replay: sends each frame JPEG before its world record', async () => {
  const dir = tmpDir();
  const file = path.join(dir, 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0,"n":1}\n{"t_ns":20000000,"n":2}\n');
  const frames = path.join(dir, 'frames');
  fs.mkdirSync(frames);
  const jpeg0 = Buffer.from([0xff, 0xd8, 0x01, 0xff, 0xd9]);
  const jpeg1 = Buffer.from([0xff, 0xd8, 0x02, 0xff, 0xd9]);
  fs.writeFileSync(path.join(frames, '000000.jpg'), jpeg0);
  fs.writeFileSync(path.join(frames, '000001.jpg'), jpeg1);

  const bridge = await startBridge({ wsPort: 0, replayFile: file, framesDir: frames });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  await once(ws, 'open');
  const msgs = await collect(ws, 6);
  ws.close();
  bridge.close();

  // Replay ticks before the client connects, so the phase varies: assert each
  // frame JPEG is sent immediately before the world record it depicts.
  const jpegs = { 1: jpeg0, 2: jpeg1 };
  let pairs = 0;
  for (let i = 0; i + 1 < msgs.length; i++) {
    if (!Buffer.isBuffer(msgs[i]) || typeof msgs[i + 1] !== 'string') continue;
    const record = JSON.parse(msgs[i + 1]);
    assert.ok(msgs[i].equals(jpegs[record.n]), `frame before n=${record.n} must be its JPEG`);
    pairs++;
  }
  assert.ok(pairs >= 3, `expected at least 3 frame/record pairs, got ${pairs}`);
});

test('replay: a missing frame file is skipped, not fatal', async () => {
  const dir = tmpDir();
  const file = path.join(dir, 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0,"n":1}\n{"t_ns":20000000,"n":2}\n');
  const frames = path.join(dir, 'frames');
  fs.mkdirSync(frames); // no JPEG files at all

  const bridge = await startBridge({ wsPort: 0, replayFile: file, framesDir: frames });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  await once(ws, 'open');
  const msgs = await collect(ws, 3);
  ws.close();
  bridge.close();

  assert.ok(msgs.every((m) => typeof m === 'string'));
});

test('replay: loops a file to dashboards', async () => {
  const file = path.join(tmpDir(), 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0,"n":1}\n{"t_ns":20000000,"n":2}\n');
  const bridge = await startBridge({ wsPort: 0, replayFile: file });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  await once(ws, 'open');
  const ns = (await collect(ws, 3)).map((m) => JSON.parse(m).n);
  ws.close();
  bridge.close();

  assert.ok(ns[0] !== ns[1] && ns[1] !== ns[2], `expected alternating messages, got ${ns}`);
});

test('switches from replay to live on request and reports the sender', async () => {
  const file = path.join(tmpDir(), 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0,"n":1}\n{"t_ns":20000000,"n":2}\n');
  const bridge = await startBridge({ wsPort: 0, udpPort: 0, replayFile: file });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  const first = status(ws);
  await once(ws, 'open');
  assert.equal((await first).source, 'replay');
  assert.equal((await first).replay, 'r');

  const live = status(ws, (b) => b.source === 'live');
  ws.send(JSON.stringify({ source: 'live' }));
  await live;

  const heard = status(ws, (b) => b.pi);
  const got = collect(ws, 1);
  const udp = dgram.createSocket('udp4');
  udp.send('{"t_ns":5,"from":"pi"}', bridge.udpPort, '127.0.0.1');
  const [msg] = await got;
  const { pi } = await heard;
  udp.close();
  ws.close();
  bridge.close();

  assert.equal(JSON.parse(msg).from, 'pi'); // live data flows; the replay loop has stopped
  assert.equal(pi.address, '127.0.0.1');
  assert.equal(pi.adapter, 'this laptop');
});

test('while replaying, live datagrams are recorded but not shown', async () => {
  const file = path.join(tmpDir(), 'r.jsonl');
  fs.writeFileSync(file, '{"t_ns":0,"n":1}\n{"t_ns":20000000,"n":2}\n');
  const bridge = await startBridge({ wsPort: 0, udpPort: 0, recordDir: tmpDir(), replayFile: file });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  await once(ws, 'open');
  const heard = status(ws, (b) => b.pi);
  const udp = dgram.createSocket('udp4');
  udp.send('{"t_ns":5,"from":"pi"}', bridge.udpPort, '127.0.0.1');
  await heard;
  const msgs = await collect(ws, 4);
  udp.close();
  ws.close();
  bridge.close();

  assert.ok(msgs.every((m) => JSON.parse(m).n), 'only replay records reach the dashboard');
  assert.equal(fs.readFileSync(bridge.file, 'utf8'), '{"t_ns":5,"from":"pi"}\n');
});

test('ignores requests it does not know, and replay when none is loaded', async () => {
  const bridge = await startBridge({ wsPort: 0, udpPort: 0 });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`);
  const first = status(ws);
  await once(ws, 'open');
  assert.deepEqual([(await first).source, (await first).replay], ['live', null]);
  for (const bad of ['{"source":"../../etc/passwd"}', '{"source":"replay"}', 'not json']) ws.send(bad);
  const next = await status(ws); // the next 1 s heartbeat
  ws.close();
  bridge.close();

  assert.equal(next.source, 'live');
});
