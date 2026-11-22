import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { eventsFromLog } from './events.js';

const replay = (name) =>
  fs.readFileSync(new URL(`../../samples/${name}`, import.meta.url), 'utf8').trim().split('\n')
    .map((line, i) => ({ at: i * 100, world: JSON.parse(line) }));
const texts = (items, first) => eventsFromLog(items, first).map((e) => e.text);

test('the simulator recording tells the slay-percept story with HOLD window and restart time', () => {
  const items = replay('sim-reach-lost.jsonl');
  assert.deepEqual(texts(items), [
    'LIVE',
    'percept down',
    'HOLD +0.0 s',
    'LOST +0.5 s',
    'percept back after 3.2 s',
    'LIVE',
  ]);
  const kill = eventsFromLog(items, 1000).find((e) => e.kind === 'down');
  assert.equal(kill.index, 1000 + items.findIndex((it) => it.world.health?.procs?.percept?.alive === false));
});

test('a looping replay never pairs a kill with the next loop', () => {
  const items = replay('dev-reach.jsonl'); // ends with percept still down, then the loop restarts the clock
  const once = texts(items);
  assert.ok(once.includes('percept down'));
  assert.deepEqual(texts([...items, ...items]), [...once, ...once]);
});

test('messages without health or mode keep the last known state', () => {
  const up = { t_ns: 1e9, mode: 'LIVE', health: { procs: { percept: { alive: true } } } };
  const targetOnly = { t_ns: 2e9, target: { name: 'keys' } };
  const down = { t_ns: 3e9, mode: 'LIVE', health: { procs: { percept: { alive: false } } } };
  const items = [up, targetOnly, down, { ...targetOnly, t_ns: 3.5e9 }, { ...up, t_ns: 4e9 }].map((world, at) => ({ at, world }));
  assert.deepEqual(texts(items), ['percept down', 'percept back after 1.0 s']);
});
