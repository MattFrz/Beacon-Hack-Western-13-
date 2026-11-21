import { useRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';

// Display guesses, not telemetry: chest height, a 30° downward pitch, Camera Module 3 standard lens.
// shortcut: hard-coded; switch to intrinsics and pitch if telemd ever sends them.
const CAM_POS = [0, 1.3, -0.12];
const CAM_PITCH = (30 * Math.PI) / 180;
const FOV_H = (66 * Math.PI) / 180;
const FOV_V = (41 * Math.PI) / 180;

const COLORS = { target: '#ffb020', object: '#4ea1ff', hand: '#ff5fa2', LIVE: '#34c759', HOLD: '#ffb020' };
const BODY = '#56606e';

// telemd sends null for a position that is not finite, so check before drawing or measuring.
const isVec = (v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const labelFor = (name, v) => (isVec(v) ? `${name} ${Math.hypot(...v).toFixed(2)} m` : name);

export default function Scene({ world }) {
  const { hand, target, mode, t_ns } = world ?? {};
  const objects = world?.objects ?? [];
  // drei <Html> labels unmount their own React root synchronously, which React 19 reports as an error.
  // So markers stay mounted once seen (objects come and go while scrubbing, the hand while reaching) and hide instead.
  const seenIds = useRef(new Set());
  for (const o of objects) seenIds.current.add(o.id);
  // telemd may send the bound target without objects[]; draw it on its own unless an object row already shows it.
  const targetAlone = Boolean(target) && !objects.some((o) => o.id === target.id);
  return (
    <Canvas camera={{ position: [1.6, 2.0, 1.2], fov: 45 }}>
      <color attach="background" args={['#0f1318']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[2, 4, 3]} intensity={1.5} />
      <gridHelper args={[6, 24, '#3b4350', '#232933']} />
      <Torso />
      {/* percept reports the OpenCV camera frame (+X right, +Y down, +Z forward). Rotating it by
          pi - pitch about X lays it onto the scene (+Y up, -Z forward), so xyz_cam goes in as is. */}
      <group position={CAM_POS} rotation={[Math.PI - CAM_PITCH, 0, 0]}>
        <Frustum />
        {[...seenIds.current].map((id) => {
          const o = objects.find((x) => x.id === id);
          return (
            <Marker
              key={id}
              visible={Boolean(o)}
              position={o?.xyz_cam}
              color={id === target?.id ? COLORS.target : COLORS.object}
              faded={o && (!o.in_latest_boxes || t_ns - o.last_seen_ns > 1e9)}
              label={o && labelFor(o.name, o.xyz_cam)}
            />
          );
        })}
        <Marker
          visible={targetAlone}
          position={target?.xyz_cam}
          color={COLORS.target}
          faded={target && t_ns - target.last_seen_ns > 1e9}
          label={target && labelFor(target.name, target.xyz_cam)}
        />
        <Marker visible={Boolean(hand)} position={hand?.xyz_cam} color={COLORS.hand} size={0.025} label="hand" labelBelow />
        {isVec(hand?.xyz_cam) && isVec(target?.xyz_cam) && COLORS[mode] && (
          <Line
            points={[hand.xyz_cam, target.xyz_cam]}
            color={COLORS[mode]}
            lineWidth={2}
            dashed={mode === 'HOLD'}
            dashSize={0.02}
            gapSize={0.015}
          />
        )}
      </group>
      <OrbitControls target={[0, 0.9, -0.5]} makeDefault />
    </Canvas>
  );
}

function Torso() {
  return (
    <>
      <mesh position={[0, 1.15, 0]} scale={[1, 1, 0.6]}>
        <capsuleGeometry args={[0.17, 0.4, 8, 16]} />
        <meshStandardMaterial color={BODY} />
      </mesh>
      <mesh position={[0, 1.65, 0]}>
        <sphereGeometry args={[0.11, 24, 16]} />
        <meshStandardMaterial color={BODY} />
      </mesh>
      <mesh position={CAM_POS}>
        <boxGeometry args={[0.05, 0.05, 0.03]} />
        <meshStandardMaterial color="#dddddd" />
      </mesh>
    </>
  );
}

// The camera's field of view as a wireframe pyramid, in camera coordinates.
function Frustum({ length = 0.9 }) {
  const w = length * Math.tan(FOV_H / 2);
  const h = length * Math.tan(FOV_V / 2);
  const [a, b, c, d] = [[-w, -h, length], [w, -h, length], [w, h, length], [-w, h, length]];
  const o = [0, 0, 0];
  return (
    <Line
      points={[o, a, o, b, o, c, o, d, a, b, b, c, c, d, d, a]}
      segments
      color="#8899aa"
      lineWidth={1}
      transparent
      opacity={0.6}
    />
  );
}

function Marker({ position = [0, 0, 0], visible = true, color, label, faded = false, size = 0.035, labelBelow = false }) {
  // <Html> picks its DOM target from r3f's event system, which connects just after startup; a label
  // mounted before that gets re-created (the same React 19 unmount error), so wait for it.
  const ready = useThree((s) => Boolean(s.events.connected));
  if (!isVec(position)) [position, visible] = [[0, 0, 0], false];
  return (
    <group position={position} visible={visible}>
      <mesh>
        <sphereGeometry args={[size, 24, 16]} />
        <meshStandardMaterial color={color} transparent opacity={faded ? 0.35 : 1} />
      </mesh>
      {/* -Y is up inside the camera group; the hand's label goes below so it never covers the target's */}
      {ready && (
        <Html position={[0, labelBelow ? size + 0.035 : -size - 0.03, 0]} center className="label">
          {visible ? label : null}
        </Html>
      )}
    </group>
  );
}
