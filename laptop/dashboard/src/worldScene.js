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
  return (world?.objects ?? [])
    .map((o) => {
      const position = worldPoint(o);
      if (!position) return null;
      const stale = isNum(tNs) && isNum(o.last_seen_ns) && tNs - o.last_seen_ns > 1e9;
      return {
        id: o.id ?? o.name,
        name: o.name ?? String(o.id ?? 'object'),
        position,
        faded: o.in_latest_boxes === false || stale,
        label: `${o.name ?? 'object'} ${norm(o.xyz_world).toFixed(2)} m`,
      };
    })
    .filter(Boolean);
}

export function worldHand(world) {
  return worldPoint(world?.hand);
}

export function worldTarget(world) {
  return worldPoint(world?.target);
}

export function crumbsToScene(world) {
  return (world?.crumbs ?? []).map(worldPoint).filter(Boolean);
}
