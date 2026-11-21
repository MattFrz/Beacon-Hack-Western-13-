import assert from 'node:assert/strict';
import test from 'node:test';
import {
  crumbsToScene,
  poseSceneMatrix,
  poseTranslation,
  toScene,
  wearerState,
  worldHand,
  worldObjects,
  worldTarget,
} from './worldScene.js';

test('toScene converts OpenCV world coordinates to three.js coordinates', () => {
  assert.deepEqual(toScene([1, -2, 3]), [1, 2, -3]);
});

test('poseTranslation reads row-major world-from-camera translation', () => {
  const pose = { valid: true, T_world_from_cam: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] };
  assert.deepEqual(poseTranslation(pose), [0, 0, 0]);
  pose.T_world_from_cam[3] = 1.25;
  pose.T_world_from_cam[7] = -0.4;
  pose.T_world_from_cam[11] = 2.5;
  assert.deepEqual(poseTranslation(pose), [1.25, -0.4, 2.5]);
});

test('poseSceneMatrix converts an identity pose into an identity scene matrix', () => {
  const pose = {
    valid: true,
    T_world_from_cam: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  };
  assert.deepEqual(poseSceneMatrix(pose), [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
});

test('poseSceneMatrix emits column-major translation for Three.js fromArray', () => {
  const pose = {
    valid: true,
    T_world_from_cam: [
      1, 0, 0, -0.02,
      0, 1, 0, 0.01,
      0, 0, 1, 0.02,
      0, 0, 0, 1,
    ],
  };
  const m = poseSceneMatrix(pose);
  // OpenCV translation [-0.02, 0.01, 0.02] -> scene [-0.02, -0.01, -0.02]
  // Three.js stores translation at column-major indices 12, 13, 14.
  assert.equal(m[12], -0.02);
  assert.equal(m[13], -0.01);
  assert.equal(m[14], -0.02);
  assert.equal(m[15], 1);
  assert.equal(m[3], 0);
  assert.equal(m[7], 0);
  assert.equal(m[11], 0);
});

test('wearerState freezes the last position when pose is invalid', () => {
  const validPose = {
    valid: true,
    age_ns: 10,
    T_world_from_cam: [1, 0, 0, 1, 0, 1, 0, 2, 0, 0, 1, 3, 0, 0, 0, 1],
  };
  const first = wearerState(validPose, null);
  assert.deepEqual(first.position, [1, -2, -3]);
  assert.equal(first.valid, true);

  const lost = wearerState({ valid: false, age_ns: 99 }, first.position);
  assert.deepEqual(lost.position, [1, -2, -3]);
  assert.equal(lost.valid, false);
  assert.equal(lost.age_ns, 99);
});

test('worldObjects uses xyz_world and skips objects without it', () => {
  const world = {
    t_ns: 1000,
    objects: [
      { id: 1, name: 'keys', xyz_world: [0.1, 0.2, 0.3], xyz_cam: [9, 9, 9], in_latest_boxes: true, last_seen_ns: 900 },
      { id: 2, name: 'bottle', xyz_cam: [1, 1, 1], in_latest_boxes: true, last_seen_ns: 1000 },
    ],
    target: { id: 1 },
  };
  const objects = worldObjects(world);
  assert.equal(objects.length, 1);
  assert.deepEqual(objects[0].position, [0.1, -0.2, -0.3]);
  assert.equal(objects[0].faded, false);
});

test('worldHand and worldTarget use world coordinates', () => {
  const world = {
    hand: { xyz_world: [0.2, 0.3, 0.4] },
    target: { xyz_world: [0.5, 0.6, 0.7] },
  };
  assert.deepEqual(worldHand(world), [0.2, -0.3, -0.4]);
  assert.deepEqual(worldTarget(world), [0.5, -0.6, -0.7]);
});

test('crumbsToScene maps only valid xyz_world points', () => {
  const world = {
    crumbs: [{ xyz_world: [1, 2, 3], t_ns: 1 }, { xyz_cam: [4, 5, 6], t_ns: 2 }],
  };
  assert.deepEqual(crumbsToScene(world), [[1, -2, -3]]);
});
