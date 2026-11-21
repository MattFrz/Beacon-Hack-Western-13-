// Writes dev-reach.jsonl: a hand-made 9 s replay so the dashboard can be built without the Pi.
// WALK cue, then the hand reaches the keys (ticks speed up, then a continuous tone), then
// `slay percept` at 6 s: the target goes HOLD, then LOST. Built on world.sample.json, so every
// field is present. Stopgap until Matt's replay generator. Regenerate: node make-dev-reach.js
import fs from 'node:fs';

const sample = JSON.parse(fs.readFileSync(new URL('world.sample.json', import.meta.url), 'utf8'));
const lerp = (a, b, k) => a.map((v, i) => +(v + (b[i] - v) * k).toFixed(3));
const dist = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));
const toWorld = (p) => p.map((v, i) => +(v + [-0.02, 0.01, 0.02][i]).toFixed(3)); // the sample pose's translation

const T0 = 500e9; // Pi CLOCK_MONOTONIC ns of the first line; lines are 100 ms apart, like telemd at 10 Hz
const KILL = 60; // line where percept is killed (6 s)
const keys = sample.objects[0].xyz_cam;
const handStart = [0.15, 0.11, 0.28]; // hand entering the bottom of the frame, ~0.28 m from the keys
const lines = [];

for (let i = 0; i < 90; i++) {
  const t_ns = T0 + i * 1e8;
  const alive = i < KILL;
  const cycle = Math.floor(Math.min(i, KILL - 1) / 3); // percept publishes a bundle every ~300 ms
  const seen = T0 + cycle * 3e8 - 2.5e8; // capture time of that bundle's frame
  const age = (t_ns - seen) / 1e9;
  const mode = age < 1.0 ? 'LIVE' : age < 1.5 ? 'HOLD' : 'LOST';

  const hand = cycle >= 7 ? lerp(handStart, keys, 0.71 * Math.min((cycle - 7) / 10, 1)) : null;
  const d = hand ? dist(hand, keys) : null;
  const law = mode === 'LOST' ? 'LOST' : hand ? 'REACH' : 'WALK';
  const reach = law === 'REACH';
  const intervalMs = reach ? 80 + (720 * (Math.min(d, 0.6) - 0.15)) / 0.45 : null; // 800 ms at 0.6 m -> 80 ms at 0.15 m
  const frame_id = 9000 + cycle;

  lines.push({
    ...sample,
    t_ns,
    seq: { percept: 1800 + 2 * cycle, voiced: 12, guided: 30000 + 12 * i },
    mode,
    law,
    cue: {
      caption: law === 'WALK' ? 'Keys. About one metre ahead, a little right.' : law === 'LOST' ? 'I lost the target.' : null,
      clip_ids: [],
      tick_hz: reach && d >= 0.15 ? +(1000 / intervalMs / (mode === 'HOLD' ? 2 : 1)).toFixed(1) : null, // HOLD ticks slower
      pan: reach ? +Math.max(-1, Math.min(1, (keys[0] - hand[0]) / 0.15)).toFixed(2) : 0,
      continuous: reach && d < 0.15,
    },
    intent: { ...sample.intent, t_ns: T0 - 1e9 },
    target: { ...sample.target, last_seen_ns: seen, frame_id },
    hand: hand && { xyz_cam: hand, xyz_world: toWorld(hand), conf: 0.9, t_ns: seen, frame_id },
    d_m: hand && +d.toFixed(3),
    objects: sample.objects.map((o) => ({ ...o, last_seen_ns: seen, frame_id })),
    pose: { ...sample.pose, t_ns: seen, age_ns: t_ns - seen },
    health: {
      ...sample.health,
      procs: {
        supervisor: { alive: true, hb_ns: t_ns - 1e7 },
        camd: { alive: true, hb_ns: t_ns - 2e7 },
        guided: { alive: true, hb_ns: t_ns - 5e6 },
        percept: { alive, hb_ns: seen + 2.5e8 },
        voiced: { alive: true, hb_ns: T0 - 1e9 },
      },
      timing: { misses_16ms: 0, worst_late_us: 380 + Math.floor(i / 30) * 12 }, // a running worst: only steps up
    },
  });
}

fs.writeFileSync(new URL('dev-reach.jsonl', import.meta.url), lines.map((l) => JSON.stringify(l)).join('\n') + '\n');
console.log(`wrote dev-reach.jsonl: ${lines.length} lines`);
