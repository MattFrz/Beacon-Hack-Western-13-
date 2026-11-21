import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { CLIP_NAMES, captionFromClips } from './clips.js';

test('clip names follow enum beacon_clip in include/beacon.h', () => {
  const header = fs.readFileSync(new URL('../../../include/beacon.h', import.meta.url), 'utf8');
  const body = header.match(/enum beacon_clip \{([\s\S]*?)\};/)[1].replace(/\/\*[\s\S]*?\*\//g, '');
  const names = [...body.matchAll(/BEACON_CLIP_(\w+)/g)].map((m) => m[1]).filter((n) => n !== 'COUNT');
  assert.deepEqual(CLIP_NAMES, names);
});

test('captionFromClips speaks the target name and skips unknown ids', () => {
  const id = (name) => CLIP_NAMES.indexOf(name);
  const walk = ['OBJECT_NAME', 'ABOUT', 'NUM_2', 'METRES', 'AHEAD', 'A_LITTLE', 'LEFT'].map(id);
  assert.equal(captionFromClips(walk, 'keys'), 'Keys about two metres ahead a little left');
  assert.equal(captionFromClips([id('LOST_TARGET'), 999], 'keys'), 'I lost the target.');
  assert.equal(captionFromClips([], 'keys'), null);
});
