import { test } from 'node:test';
import assert from 'node:assert/strict';
import dgram from 'node:dgram';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';
import { parseWorld, loadReplay, gapMs, startBridge } from './bridge.js';

const sampleFile = fileURLToPath(new URL('../samples/world.sample.json', import.meta.url));
const tmpDir = () => fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-'));

// The next n WebSocket messages: strings for text frames, Buffers for binary frames.
function collect(ws, n) {
  return new Promise((resolve, reject) => {
    const got = [];
    const timer = setTimeout(() => reject(new Error(`timed out with ${got.length}/${n} messages`)), 2000);
    ws.on('message', (data, isBinary) => {
      got.push(isBinary ? data : data.toString());
      if (got.length === n) {
        clearTimeout(timer);
        resolve(got);
      }
    });
  });
}

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
  assert.deepEqual(msgs.find((m) => Buffer.isBuffer(m)), jpeg);
  assert.equal(fs.readFileSync(bridge.file, 'utf8'), line + '\n');
});

test('rejects pages from other sites', async () => {
  const bridge = await startBridge({ wsPort: 0, replayFile: sampleFile });
  const ws = new WebSocket(`ws://127.0.0.1:${bridge.wsPort}`, { origin: 'https://example.com' });
  const [err] = await once(ws, 'error');
  bridge.close();

  assert.match(err.message, /401/);
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
