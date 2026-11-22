import { useRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';
import { Matrix4 } from 'three';
import {
  crumbsToScene,
  displayPose,
  poseSceneMatrix,
  wearerState,
  worldHand,
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
  LIVE: '#34c759',
  HOLD: '#ffb020',
};

// telemd sends null for a position that is not finite, so check before measuring.
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const norm = (v) => Math.hypot(...v);

export default function Scene({ world }) {
  const { mode } = world ?? {};
  const objects = worldObjects(world);
  const hand = worldHand(world);
  const target = worldTarget(world);
  const crumbs = crumbsToScene(world);

  const seenIds = useRef(new Set());
  const lastWearerPosition = useRef(null);
  for (const o of objects) seenIds.current.add(o.id);

  const pose = displayPose(world);
  const nextWearer = wearerState(pose, lastWearerPosition.current);
  if (nextWearer.position) lastWearerPosition.current = nextWearer.position;
  const wearer = { ...nextWearer, position: lastWearerPosition.current };
  const poseMatrix = poseSceneMatrix(pose);

  // telemd can send a bound target without objects[]; draw it on its own unless an object row already shows it.
  const targetId = world?.target?.id;
  const targetAlone = Boolean(target) && !objects.some((o) => o.id === targetId);
  const targetFaded =
    world?.target?.in_latest_boxes === false ||
    (isNum(world?.t_ns) && isNum(world?.target?.last_seen_ns) && world.t_ns - world.target.last_seen_ns > 1e9);

  return (
    <Canvas camera={{ position: [2.0, 2.2, 2.0], fov: 45 }}>
      <color attach="background" args={['#18191b']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[2, 4, 3]} intensity={1.5} />
      <gridHelper args={[10, 40, '#3d3f44', '#26282b']} />

      {crumbs.map((p, i) => (
        <mesh key={`crumb-${i}`} position={p}>
          <sphereGeometry args={[0.012, 10, 8]} />
          <meshStandardMaterial color={COLORS.crumb} transparent opacity={0.45} />
        </mesh>
      ))}

      {[...seenIds.current].map((id) => {
        const o = objects.find((x) => x.id === id);
        return (
          <Marker
            key={id}
            visible={Boolean(o)}
            position={o?.position}
            color={id === world?.target?.id ? COLORS.target : COLORS.object}
            faded={o?.faded}
            label={o?.label}
          />
        );
      })}

      {hand && <Marker position={hand} color={COLORS.hand} size={0.025} label="hand" labelBelow />}

      {targetAlone && (
        <Marker
          position={target}
          color={COLORS.target}
          faded={targetFaded}
          label={`${world?.target?.name ?? 'target'} ${norm(target).toFixed(2)} m`}
        />
      )}

      {hand && target && COLORS[mode] && (
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
          <Marker position={wearer.position} color={COLORS.wearer} size={0.045} label={wearer.valid ? 'wearer' : 'pose lost'} labelBelow />
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

function Marker({ position = [0, 0, 0], visible = true, color, label, faded = false, size = 0.035, labelBelow = false }) {
  // <Html> picks its DOM target from r3f's event system, which connects just after startup; a label
  // mounted before that gets re-created (the same React 19 unmount error), so wait for it.
  // zIndexRange keeps labels under the top bar (10) and the panels (20); drei's default draws them over everything.
  const ready = useThree((s) => Boolean(s.events.connected));
  return (
    <group position={position} visible={visible}>
      <mesh>
        <sphereGeometry args={[size, 24, 16]} />
        <meshStandardMaterial color={color} transparent opacity={faded ? 0.35 : 1} />
      </mesh>
      {ready && (
        <Html position={[0, labelBelow ? size + 0.035 : -size - 0.03, 0]} center className="label" zIndexRange={[9, 0]}>
          {visible ? label : null}
        </Html>
      )}
    </group>
  );
}
