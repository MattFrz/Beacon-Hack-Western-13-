import { Highlight, HighlightItem } from '@animate-ui/react/primitives/effects/highlight';
import { RollingText } from '@animate-ui/react/primitives/texts/rolling';
import { SlidingNumber } from '@animate-ui/react/primitives/texts/sliding-number';
import { useState } from 'react';
import { captionFromClips } from './clips.js';
import Events from './Events.jsx';
import Scene from './Scene.jsx';
import Scrubber from './Scrubber.jsx';
import { useTelemetry } from './useTelemetry.js';
import { crumbsToScene, worldObjects } from './worldScene.js';

const MODES = ['LIVE', 'HOLD', 'LOST'];
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
// 0 means "not measured yet" for vision timings (no real YOLO run takes 0 ms), so show "–", not "0 ms".
const measured = (v) => (isNum(v) && v > 0 ? v : null);
const msAgo = (now, then) => (isNum(now) && isNum(then) ? (now - then) / 1e6 : null);
const panWord = (p) => (!isNum(p) ? '–' : p < -0.1 ? 'left' : p > 0.1 ? 'right' : 'centre');

// A live number whose digits roll to each new value; '–' when telemetry has none.
function Num({ value, digits = 0, unit = '' }) {
  if (!isNum(value)) return '–';
  return (
    <>
      <SlidingNumber number={value} decimalPlaces={digits} initiallyStable />
      {unit}
    </>
  );
}

// Words that change (law, intent, spoken sentence) roll in letter by letter.
function Rolling({ text, stagger = 0.03 }) {
  if (!text) return '–';
  return <RollingText key={text} text={text} transition={{ duration: 0.3, delay: stagger, ease: 'easeOut' }} />;
}

export default function App() {
  const { log, world, frameUrl, connected, stale } = useTelemetry();
  const [cursor, setCursor] = useState(null); // null = follow live, else the history index being viewed
  const paused = cursor != null;
  const shown = paused ? log.items[Math.max(cursor, log.first) - log.first]?.world : world;
  const hasData = paused ? Boolean(shown) : Boolean(connected && !stale && world);
  const w = shown ?? {};
  const mode = hasData && MODES.includes(w.mode) ? w.mode : null;
  const health = w.health ?? {};

  return (
    <div className="app">
      <header>
        <Highlight mode="parent" controlledItems value={mode} click={false} className="mode-hl" containerClassName="modes">
          {MODES.map((m) => (
            <HighlightItem key={m} value={m} activeClassName={`hl-${m}`}>
              <div className={m === mode ? 'mode on' : 'mode'}>{m}</div>
            </HighlightItem>
          ))}
        </Highlight>
        {paused ? <div className="paused-pill">PAUSED</div> : !hasData && <div className="nodata">NO DATA</div>}
        <div>
          Law <b><Rolling text={w.law} /></b>
        </div>
        <div>
          Intent <b><Rolling text={w.intent?.kind} /></b> {w.intent?.candidates?.join(', ')}
        </div>
        <div className="link">
          {connected ? 'bridge connected' : 'bridge not running: start it in laptop/bridge (npm run replay:dev)'}
        </div>
      </header>

      <main className={hasData ? '' : 'stale'}>
        <Scene world={shown} />
        <Caption law={w.law} cue={w.cue} targetName={w.target?.name} />
      </main>
      <Scrubber log={log} cursor={cursor} setCursor={setCursor} />

      <aside>
        <h2>Target</h2>
        {w.target ? (
          <dl>
            <dt>Name</dt>
            <dd>{w.target.name}</dd>
            <dt>Hand to target</dt>
            <dd><Num value={w.d_m} digits={2} unit=" m" /></dd>
            <dt>From camera</dt>
            <dd><Num value={w.target.xyz_cam && Math.hypot(...w.target.xyz_cam)} digits={2} unit=" m" /></dd>
            <dt>Last seen</dt>
            <dd><Num value={msAgo(w.t_ns, w.target.last_seen_ns)} unit=" ms ago" /></dd>
            <dt>Confidence</dt>
            <dd><Num value={w.target.conf} digits={2} /></dd>
          </dl>
        ) : (
          <p className="muted">No target bound</p>
        )}

        <h2>Map</h2>
        <dl>
          <dt>Pose</dt>
          <dd>{w.pose == null ? 'not sent' : w.pose.valid === true ? 'valid' : 'lost'}</dd>
          <dt>Pose age</dt>
          <dd><Num value={isNum(w.pose?.age_ns) ? w.pose.age_ns / 1e6 : null} digits={0} unit=" ms" /></dd>
          <dt>Object dots</dt>
          <dd>{worldObjects(w).length}</dd>
          <dt>Crumbs</dt>
          <dd>{crumbsToScene(w).length}</dd>
        </dl>

        <h2>Processes</h2>
        <ul className="procs">
          {Object.entries(health.procs ?? {}).map(([name, p]) => (
            <li key={name} className={p.alive ? 'up' : 'down'}>
              <span>{name}</span>
              {/* plain text: heartbeat ages jitter every message, so rolling digits would never settle */}
              <span>{p.alive ? `beat ${isNum(msAgo(w.t_ns, p.hb_ns)) ? Math.round(msAgo(w.t_ns, p.hb_ns)) : '–'} ms ago` : 'down'}</span>
            </li>
          ))}
        </ul>

        <h2>Events</h2>
        <Events log={log} setCursor={setCursor} />

        <h2>Timing</h2>
        <dl>
          <dt>YOLO / depth</dt>
          <dd><Num value={measured(health.last_yolo_ms)} /> / <Num value={measured(health.last_depth_ms)} unit=" ms" /></dd>
          <dt>Vision p95</dt>
          <dd><Num value={measured(health.p95_vision_ns / 1e6)} unit=" ms" /></dd>
          <dt>16 ms misses</dt>
          <dd><Num value={health.timing?.misses_16ms} /></dd>
          <dt>Worst late</dt>
          <dd><Num value={health.timing?.worst_late_us} unit=" µs" /></dd>
        </dl>

        {/* video is not kept in history, so a paused view never shows a live frame next to a past scene */}
        {frameUrl && !paused && (
          <>
            <h2>Camera</h2>
            <img src={frameUrl} alt="Latest downscaled camera frame from telemd" />
          </>
        )}
      </aside>
    </div>
  );
}

// What the wearer hears right now: the spoken sentence, or the reach ticks.
// REACH comes first: guided keeps its last spoken clips after speech stops for the reach.
function Caption({ law, cue, targetName }) {
  if (law === 'REACH' && cue) {
    return (
      <p className="caption">
        {cue.continuous ? 'Continuous tone' : <>Ticks <Num value={cue.tick_hz} digits={1} unit=" Hz" /></>}, pan{' '}
        {panWord(cue.pan)}
      </p>
    );
  }
  const text = cue?.caption ?? (cue?.clip_ids?.length ? captionFromClips(cue.clip_ids, targetName) : null);
  if (!text) return null;
  return (
    <p className="caption">
      “<Rolling text={text} stagger={0.012} />”
    </p>
  );
}
