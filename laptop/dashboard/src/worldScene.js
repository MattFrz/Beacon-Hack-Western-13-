const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const isVec3 = (v) => Array.isArray(v) && v.length >= 3 && v.slice(0, 3).every(isNum);
const norm = (v) => Math.hypot(...v);

// OpenCV world is +X right, +Y down, +Z forward. three.js is +Y up and looks down -Z.
export function toScene([x, y, z]) {
  return [x, -y, -z];
}

function worldPoint(value) {
  return isVec3(value?.xyz_world) ? toScene(value.xyz_world) : null;
}

export function poseTranslation(pose) {
  const t = pose?.T_world_from_cam;
  if (!Array.isArray(t) || t.length < 16 || !t.slice(0, 16).every(isNum)) return null;
  return [t[3], t[7], t[11]]; // row-major translation
}

export function poseSceneMatrix(pose) {
  const t = pose?.T_world_from_cam;
  if (!pose?.valid || !Array.isArray(t) || t.length < 16 || !t.slice(0, 16).every(isNum)) return null;
  // Conjugate by diag(1, -1, -1, 1), the OpenCV-world -> three.js world change of basis.
  // Telemetry T is row-major; Three.js Matrix4.fromArray is column-major.
  const signs = [1, -1, -1, 1];
  const out = new Array(16);
  for (let r = 0; r < 4; r += 1) {
    for (let c = 0; c < 4; c += 1) {
      const value = t[r * 4 + c] * signs[r] * signs[c];
      out[c * 4 + r] = value === 0 ? 0 : value;
    }
  }
  return out;
}

// telemd does not send pose yet. Before odometry, percept's pose is identity and xyz_world = xyz_cam
// (probe_to_world.py phase A), so a missing pose means the wearer's camera sits at the world origin.
const PHASE_A_POSE = { valid: true, T_world_from_cam: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] };

export function displayPose(world) {
  return world && world.pose == null ? PHASE_A_POSE : world?.pose;
}

export function wearerState(pose, previous = null) {
  const translation = pose?.valid ? poseTranslation(pose) : null;
  return {
    position: translation ? toScene(translation) : previous,
    valid: Boolean(translation),
    age_ns: isNum(pose?.age_ns) ? pose.age_ns : null,
  };
}

export function worldObjects(world) {
  const tNs = world?.t_ns;
  return (world?.objects ?? world?.scene?.objects ?? [])
    .map((o) => {
      const position = worldPoint(o);
      if (!position) return null;
      const stale = isNum(tNs) && isNum(o.last_seen_ns) && tNs - o.last_seen_ns > 1e9;
      return {
        id: o.id ?? o.name,
        name: o.name ?? String(o.id ?? 'object'),
        position,
        seen: o.last_seen_ns ?? (o.in_latest_boxes === false ? 0 : tNs) ?? 0,
        faded: !(o.in_latest_boxes ?? !stale),
        range: norm(isVec3(o.xyz_cam) ? o.xyz_cam : o.xyz_world),
        label: `${o.name ?? 'object'} ${norm(isVec3(o.xyz_cam) ? o.xyz_cam : o.xyz_world).toFixed(2)} m`,
      };
    })
    .filter(Boolean);
}

// Cluster newest sightings first so older duplicate rows cannot move a marker back.
export function rememberObjects(memory, objects) {
  const entries = memory.map(m => ({ ...m, live: false, faded: true }));
  for (const o of objects) {
    entries.push({ ...o, sourceId: o.id, live: !o.faded });
  }
  entries.sort((a, b) => (b.seen ?? 0) - (a.seen ?? 0) || Number(b.live) - Number(a.live)
    || Number(Boolean(a.key)) - Number(Boolean(b.key)));
  const markers = [];
  for (const entry of entries) {
    const match = markers.find(m => m.name === entry.name && Math.hypot(
      m.position[0] - entry.position[0], m.position[1] - entry.position[1], m.position[2] - entry.position[2],
    ) <= 0.5);
    if (match) {
      if (entry.key && !match.key) match.key = entry.key;
    } else {
      markers.push(entry);
    }
  }
  for (const marker of markers) {
    marker.key ??= JSON.stringify([marker.name, marker.position]);
  }
  const order = new Map(memory.map((entry, i) => [entry.key, i]));
  return markers.sort((a, b) => (order.get(a.key) ?? Infinity) - (order.get(b.key) ?? Infinity));
}

export function worldHand(world) {
  return worldPoint(world?.hand);
}

export function worldTarget(world) {
  return worldPoint(world?.target);
}

// Which objects[] row is the bound target. guided numbers its target while percept names objects
// ("bottle-1"), so when no id matches, the row with the target's name at the target's position is it.
export function targetObjectId(world, objects = worldObjects(world)) {
  const t = world?.target;
  const p = worldTarget(world);
  if (!t || !p) return null;
  const near = (o) => o.name === t.name && Math.hypot(o.position[0] - p[0], o.position[1] - p[1], o.position[2] - p[2]) < 0.05;
  return (objects.find((o) => o.id === t.id) ?? objects.find(near))?.id ?? null;
}

export function crumbsToScene(world) {
  return (world?.crumbs ?? []).map(worldPoint).filter(Boolean);
}

// The wearer's walked path, kept by the dashboard from the pose telemd sends (nothing writes
// crumbs live). A point every TRAIL_STEP_M of movement; a jump bigger than TRAIL_JUMP_M between
// two packets is a tracking glitch, not a step, so it is skipped. A new pose_epoch means the
// tracker re-based its world origin: the old points no longer line up, so the drawn trail
// restarts, while the walked distance keeps adding up.
export const TRAIL_STEP_M = 0.05;
export const TRAIL_JUMP_M = 1.5;
const TRAIL_MAX = 3000;

export function extendTrail(trail, pose) {
  const prev = trail ?? { points: [], epoch: null, walked_m: 0 };
  const t = pose?.valid ? poseTranslation(pose) : null;
  if (!t) return prev;
  const point = toScene(t);
  const epoch = isNum(pose.pose_epoch) ? pose.pose_epoch : null;
  if (epoch !== prev.epoch) return { points: [point], epoch, walked_m: prev.walked_m };
  const last = prev.points[prev.points.length - 1];
  if (!last) return { ...prev, points: [point] };
  const step = Math.hypot(point[0] - last[0], point[1] - last[1], point[2] - last[2]);
  if (step < TRAIL_STEP_M || step > TRAIL_JUMP_M) return prev;
  const points = prev.points.length >= TRAIL_MAX ? prev.points.slice(1) : prev.points.slice();
  points.push(point);
  return { points, epoch, walked_m: prev.walked_m + step };
}
