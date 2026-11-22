import { readFileSync } from 'node:fs';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The bridge identifies bundled recordings by id. Read their endpoints at build time so
// the dashboard can show the correct playhead even when it joins halfway through a loop.
const recordings = { vid360: 'vid360-look-around', reach: 'sim-reach-lost' };
const bounds = Object.fromEntries(Object.entries(recordings).map(([id, file]) => {
  const lines = readFileSync(new URL(`../samples/${file}.jsonl`, import.meta.url), 'utf8').trim().split(/\r?\n/);
  return [id, [JSON.parse(lines[0]).t_ns, JSON.parse(lines.at(-1)).t_ns]];
}));

export default defineConfig({ plugins: [react()], define: { __REPLAY_BOUNDS__: JSON.stringify(bounds) } });
