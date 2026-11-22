import { useRef } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';
import { Matrix4 } from 'three';
import {
  crumbsToScene,
  displayPose,
  extendTrail,
  poseSceneMatrix,
  targetObjectId,
  wearerState,
  worldHand,
  rememberObjects,
  worldObjects,
  worldTarget,
} from './worldScene.js';

// Display guesses, not telemetry: Camera Module 3 standard lens. Used only for the wearer cone.
const FOV_H = (66 * Math.PI) / 180;
const FOV_V = (41 * Math.PI) / 180;

const COLORS = {
  target: '#ffb020',
  object: '#4ea1ff',
  hand: '#ff5fa2',
  wearer: '#f2f5f8',
  crumb: '#7b8794',
  trail: '#5ac8fa',
  LIVE: '#34c759',
  HOLD: '#ffb020',
};

// telemd sends null for a position that is not finite, so check before measuring.
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const norm = (v) => Math.hypot(...v);

export default function Scene({ world, latest, hand, handOpacity, paused }) {
  const { mode } = world ?? {};
  const objects = worldObjects(world);
  const measuredHand = worldHand(world);
  const target = worldTarget(world);
  const crumbs = crumbsToScene(world);

  // The map only grows: objects and the camera's last pose survive dropped frames, LOST and pose loss.
  // Only remounting the Scene (the Reset map button, or switching source) clears it.
  const memory = useRef({ world: undefined, objects: [], matrix: null, wearer: null, trail: null });
  const m = memory.current;
  if (latest !== m.world) {
    const rewind = latest?.t_ns < m.world?.t_ns;
    const pose = displayPose(latest);
    m.objects = rememberObjects(rewind ? [] : m.objects, worldObjects(latest));
    m.wearer = wearerState(pose, rewind ? null : m.wearer).position;
    m.matrix = poseSceneMatrix(pose) ?? (rewind ? null : m.matrix);
    m.trail = extendTrail(rewind ? null : m.trail, pose);
    m.world = latest;
  }
  const pose = displayPose(world);
  const markers = paused ? rememberObjects([], objects) : m.objects;
  const wearer = wearerState(pose, paused ? null : m.wearer);
  const poseMatrix = paused ? poseSceneMatrix(pose) : m.matrix;

  // telemd can send a bound target without objects[]; draw it on its own unless an object row already shows it.
  const targetId = targetObjectId(world, objects);
  const targetMarker = target && (markers.find(o => targetId != null && o.sourceId === targetId)
    ?? markers.find(o => o.name === world.target.name && Math.hypot(...target.map((v, i) => v - o.position[i])) <= 0.5));
  const targetAlone = Boolean(target) && !targetMarker;
  const targetFaded =
    world?.target?.in_latest_boxes === false ||
    (isNum(world?.t_ns) && isNum(world?.target?.last_seen_ns) && world.t_ns - world.target.last_seen_ns > 1e9);

  return (
    <Canvas camera={{ position: [2.0, 2.2, 2.0], fov: 45 }}>
      <color attach="background" args={['#18191b']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[2, 4, 3]} intensity={1.5} />
      <gridHelper args={[10, 40, '#3d3f44', '#26282b']} />

      {m.trail?.points.length >= 2 && (
        <Line points={m.trail.points} color={COLORS.trail} lineWidth={2} transparent opacity={0.8} />
      )}

      {crumbs.map((p, i) => (
        <mesh key={`crumb-${i}`} position={p}>
          <sphereGeometry args={[0.012, 10, 8]} />
          <meshStandardMaterial color={COLORS.crumb} transparent opacity={0.45} />
        </mesh>
      ))}

      {markers.map((o) => (
        <Marker
          key={o.key}
          position={o.position}
          priority={o === targetMarker}
          color={(o === targetMarker) ? COLORS.target : COLORS.object}
          faded={o.faded}
          label={o.live || o === targetMarker ? o.label : null}
        />
      ))}

      {hand && <Marker position={hand} opacity={handOpacity} color={COLORS.hand} size={0.025} label={measuredHand ? 'hand' : null} labelBelow />}

      {targetAlone && (
        <Marker
          priority
          position={target}
          color={COLORS.target}
          faded={targetFaded}
          label={`${world?.target?.name ?? 'target'} ${norm(world.target.xyz_cam ?? target).toFixed(2)} m`}
        />
      )}

      {measuredHand && hand && target && isNum(world?.d_m) && COLORS[mode] && (
        <Line
          points={[hand, target]}
          color={COLORS[mode]}
          lineWidth={2}
          dashed={mode === 'HOLD'}
          dashSize={0.02}
          gapSize={0.015}
        />
      )}

      {wearer.position && (
        <>
          <Marker position={wearer.position} color={COLORS.wearer} size={0.045} label={wearer.valid
            ? (m.trail?.walked_m >= 0.1 ? `wearer · ${m.trail.walked_m.toFixed(1)} m walked` : 'wearer')
            : 'pose lost'} labelBelow />
          {poseMatrix ? (
            <group matrixAutoUpdate={false} matrix={new Matrix4().fromArray(poseMatrix)}>
              <Frustum />
            </group>
          ) : (
            <group position={wearer.position}>
              <Frustum />
            </group>
          )}
        </>
      )}

      <LabelVisibility />
      <OrbitControls target={wearer.position ?? [0, 0, 0]} makeDefault />
    </Canvas>
  );
}

// The camera's field of view as a wireframe pyramid in camera space. OpenCV +Z forward is scene -Z.
function Frustum({ length = 0.9 }) {
  const w = length * Math.tan(FOV_H / 2);
  const h = length * Math.tan(FOV_V / 2);
  const z = -length;
  const [a, b, c, d] = [[-w, -h, z], [w, -h, z], [w, h, z], [-w, h, z]];
  const o = [0, 0, 0];
  return (
    <Line
      points={[o, a, o, b, o, c, o, d, a, b, b, c, c, d, d, a]}
      segments
      color="#9c9ea3"
      lineWidth={1}
      transparent
      opacity={0.6}
    />
  );
}

// Orbit and zoom change which labels collide even between telemetry frames.
function LabelVisibility() {
  useFrame(({ gl }) => {
    const stage = gl.domElement.closest('.stage');
    if (!stage) return;
    const labels = [...stage.querySelectorAll('.label')]
      .sort((a, b) => Number(b.classList.contains('target-label')) - Number(a.classList.contains('target-label')));
    const boxes = labels.map(label => label.getBoundingClientRect());
    const occupied = [];
    labels.forEach((label, i) => {
      const r = boxes[i];
      const overlaps = occupied.some(b => r.left < b.right && r.right > b.left && r.top < b.bottom && r.bottom > b.top);
      label.style.visibility = overlaps ? 'hidden' : 'visible';
      if (!overlaps && r.width) occupied.push(r);
    });
  });
  return null;
}

function Marker({ position = [0, 0, 0], visible = true, color, label, priority = false, faded = false, opacity = 1, size = 0.035, labelBelow = false }) {
  // <Html> picks its DOM target from r3f's event system, which connects just after startup; a label
  // mounted before that gets re-created (the same React 19 unmount error), so wait for it.
  // zIndexRange keeps labels under the top bar (10) and the panels (20); drei's default draws them over everything.
  const ready = useThree((s) => Boolean(s.events.connected));
  return (
    <group position={position} visible={visible}>
      <mesh>
        <sphereGeometry args={[size, 24, 16]} />
        <meshStandardMaterial color={color} transparent opacity={faded ? 0.3 : opacity} />
      </mesh>
      {ready && label && (
        <Html position={[0, labelBelow ? size + 0.035 : -size - 0.03, 0]} center className={priority ? "label target-label" : "label"} zIndexRange={[9, 0]}>
          {visible ? label : null}
        </Html>
      )}
    </group>
  );
}
