import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { buildDevReach } from './make-dev-reach.js';

const sample = JSON.parse(fs.readFileSync(new URL('world.sample.json', import.meta.url), 'utf8'));
const lines = buildDevReach(sample);
const lastLive = lines.filter((line) => line.mode === 'LIVE').at(-1);

test('the first line after kill fades the held boxes and keeps their world positions', () => {
  const hold = lines[60];
  assert.equal(hold.mode, 'HOLD');
  assert.equal(hold.objects.length, 2);
  assert.ok(hold.objects.every((obj) => obj.in_latest_boxes === false));
  assert.deepEqual(hold.objects.map((obj) => obj.xyz_cam), lastLive.objects.map((obj) => obj.xyz_cam));
  assert.deepEqual(hold.objects.map((obj) => obj.xyz_world), lastLive.objects.map((obj) => obj.xyz_world));
  assert.deepEqual(hold.objects.map((obj) => obj.last_seen_ns), lastLive.objects.map((obj) => obj.last_seen_ns));
  assert.deepEqual(hold.target, { ...lastLive.target, in_latest_boxes: false });
  assert.equal(hold.d_m, lastLive.d_m);
  assert.ok(lines.slice(60).every((line) => line.mode !== 'LIVE'));
});

test('the first line at or after 1.5 s since the last live capture is an empty LOST cloud', () => {
  const lastLiveSeenNs = lastLive.target.last_seen_ns;
  const firstLost = lines.find((line) => line.t_ns - lastLiveSeenNs >= 1_500_000_000);
  assert.equal(firstLost.mode, 'LOST');
  assert.deepEqual(firstLost.objects, []);
  assert.equal(firstLost.target, null);
  assert.equal(Object.hasOwn(firstLost, 'd_m'), false);
  assert.equal(firstLost.hand, null);
});

test('lines before kill stay LIVE with fresh boxes', () => {
  const live = lines[0];
  assert.equal(live.mode, 'LIVE');
  assert.equal(live.objects.length, 2);
  assert.ok(live.objects.every((obj) => obj.in_latest_boxes === true));
});
