import { Switch } from '@animate-ui/react/primitives/base-ui/switch';
import { Button } from '@animate-ui/react/primitives/buttons/button';
import { Highlight, HighlightItem } from '@animate-ui/react/primitives/effects/highlight';
import { RollingText } from '@animate-ui/react/primitives/texts/rolling';
import { ShimmeringText } from '@animate-ui/react/primitives/texts/shimmering';
import { SlidingNumber } from '@animate-ui/react/primitives/texts/sliding-number';
import { ReducedMotionContext, useShouldReduceMotion } from '@animate-ui/react/utils/motion';
import { MotionConfig } from 'motion/react';
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { captionFromClips } from './clips.js';
import Events from './Events.jsx';
import { Collapse, Expand, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from './icons.jsx';
import Scene from './Scene.jsx';
import Scrubber from './Scrubber.jsx';
import Sidebar from './Sidebar.jsx';
import Tip from './Tip.jsx';
import { useTelemetry } from './useTelemetry.js';
import { crumbsToScene, worldObjects } from './worldScene.js';

const MODES = ['LIVE', 'HOLD', 'LOST'];
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
// 0 means "not measured yet" for vision timings (no real YOLO run takes 0 ms), so show "–", not "0 ms".
const measured = (v) => (isNum(v) && v > 0 ? v : null);
const msAgo = (now, then) => (isNum(now) && isNum(then) ? (now - then) / 1e6 : null);
const panWord = (p) => (!isNum(p) ? '–' : p < -0.1 ? 'left' : p > 0.1 ? 'right' : 'centre');

const NARROW = '(max-width: 899px)';
const REDUCE = '(prefers-reduced-motion: reduce)';
const PANELS_KEY = 'beacon.panels';
const MOTION_KEY = 'beacon.motion';
const BOTH = { left: true, right: true };
// The viewer's animation choice -> the reduced-motion setting Motion and animate-ui read.
const MOTION_SETTING = { system: 'user', on: 'never', off: 'always' };

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

// The last spoken sentence: telemd's caption, else guided's clip ids turned into words.
const spoken = (cue, targetName) => cue?.caption ?? (cue?.clip_ids?.length ? captionFromClips(cue.clip_ids, targetName) : null);

function useMedia(query) {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query);
      mql.addEventListener('change', onChange);
      return () => mql.removeEventListener('change', onChange);
    },
    () => window.matchMedia(query).matches,
  );
}

// 'system' follows the OS reduced-motion setting; 'on' and 'off' override it in this browser only.
function useMotionChoice() {
  const [choice, setChoice] = useState(() => {
    try {
      const v = localStorage.getItem(MOTION_KEY);
      if (v in MOTION_SETTING) return v;
    } catch {
      /* fall through */
    }
    return 'system';
  });
  useEffect(() => {
    document.documentElement.dataset.motion = choice; // the CSS reduced-motion rule skips 'on'
    try {
      localStorage.setItem(MOTION_KEY, choice);
    } catch {
      /* not remembered this time */
    }
  }, [choice]);
  return [choice, setChoice];
}

// Which sidebars are open: remembered per browser (a convenience only, so every storage call may fail).
function usePanels(narrow) {
  const [panels, setPanels] = useState(() => {
    try {
      const v = JSON.parse(localStorage.getItem(PANELS_KEY));
      if (typeof v?.left === 'boolean' && typeof v?.right === 'boolean') return v;
    } catch {
      /* private window or blocked storage: fall through to the default */
    }
    return window.matchMedia(NARROW).matches ? { left: false, right: false } : BOTH;
  });
  // A window that turns narrow with both panels open would show no 3D at all: close them.
  useEffect(() => {
    if (narrow) setPanels((p) => (p.left && p.right ? { left: false, right: false } : p));
  }, [narrow]);
  useEffect(() => {
    try {
      localStorage.setItem(PANELS_KEY, JSON.stringify(panels));
    } catch {
      /* not remembered this time */
    }
  }, [panels]);
  // On a narrow screen the panels cover the view, so only one is open at a time.
  const set = useCallback(
    (side, open) => setPanels((p) => (narrow && open ? { left: false, right: false, [side]: true } : { ...p, [side]: open })),
    [narrow],
  );
  return [panels, setPanels, set];
}

export default function App() {
  const { log, world, frameUrl, connected, stale } = useTelemetry();
  const [cursor, setCursor] = useState(null); // null = follow live, else the history index being viewed
  const narrow = useMedia(NARROW);
  const systemReduce = useMedia(REDUCE);
  const [motionChoice, setMotionChoice] = useMotionChoice();
  const [panels, setPanels, setPanel] = usePanels(narrow);
  const restore = useRef(BOTH);
  const setting = MOTION_SETTING[motionChoice];
  const animationsOn = motionChoice === 'on' || (motionChoice === 'system' && !systemReduce);

  const paused = cursor != null;
  const shown = paused ? log.items[Math.max(cursor, log.first) - log.first]?.world : world;
  const hasData = paused ? Boolean(shown) : Boolean(connected && !stale && world);
  const w = shown ?? {};
  const mode = hasData && MODES.includes(w.mode) ? w.mode : null;
  const health = w.health ?? {};
  const focused = !panels.left && !panels.right;

  // Focus: hide both panels for a full-screen 3D view, then bring back the ones that were open.
  const toggleFocus = useCallback(() => {
    setPanels((p) => {
      if (p.left || p.right) {
        restore.current = p;
        return { left: false, right: false };
      }
      const back = restore.current.left || restore.current.right ? restore.current : BOTH;
      return narrow ? { left: back.left, right: !back.left && back.right } : back;
    });
  }, [narrow, setPanels]);

  // Capture phase so Ctrl/Cmd+B reaches us before both animate-ui sidebar providers, which each bind it.
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        e.stopPropagation();
        toggleFocus();
      } else if (!e.ctrlKey && !e.metaKey && !e.altKey && (e.key === '[' || e.key === ']')) {
        const side = e.key === '[' ? 'left' : 'right';
        setPanel(side, !panels[side]);
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [panels, setPanel, toggleFocus]);

  return (
    <MotionScope setting={setting}>
      <div className="shell">
        <Sidebar
          side="left"
          title="Guidance"
          keys="["
          open={panels.left}
          onOpenChange={(open) => setPanel('left', open)}
          icons={{ open: <PanelLeftOpen />, close: <PanelLeftClose /> }}
        >
          <Guidance w={w} />
        </Sidebar>

        <main className="stage" data-stale={!hasData}>
          <Scene world={shown} />

          <div className="topbar">
            <div className="brand">
              <span className="mark" aria-hidden="true" />
              Beacon
            </div>
            <Highlight mode="parent" controlledItems value={mode} click={false} className="mode-hl" containerClassName="modes">
              {MODES.map((m) => (
                <HighlightItem key={m} value={m} activeClassName={`hl-${m}`}>
                  <div className={m === mode ? 'mode on' : 'mode'} aria-current={m === mode ? 'true' : undefined}>
                    {m}
                  </div>
                </HighlightItem>
              ))}
            </Highlight>
            <div className="readout">
              <span>Law</span>
              <b><Rolling text={w.law} /></b>
            </div>
            <div className="readout">
              <span>Intent</span>
              <b><Rolling text={w.intent?.kind} /></b>
              {w.intent?.candidates?.length > 0 && <em>{w.intent.candidates.join(', ')}</em>}
            </div>
            <div className="topbar-end">
              <Status connected={connected} paused={paused} hasData={hasData} />
              <Tip label={focused ? 'Bring the panels back' : 'Focus the 3D view'} keys="Ctrl B">
                <Button className="icon-btn" aria-label={focused ? 'Show the panels' : 'Focus the 3D view'} aria-pressed={focused} onClick={toggleFocus}>
                  {focused ? <Collapse /> : <Expand />}
                </Button>
              </Tip>
            </div>
          </div>

          {!connected && log.items.length === 0 && <Waiting />}

          <div className="stage-foot">
            <Caption law={w.law} cue={w.cue} targetName={w.target?.name} />
            <Scrubber log={log} cursor={cursor} setCursor={setCursor} />
          </div>
        </main>

        <Sidebar
          side="right"
          title="System"
          keys="]"
          open={panels.right}
          onOpenChange={(open) => setPanel('right', open)}
          icons={{ open: <PanelRightOpen />, close: <PanelRightClose /> }}
        >
          <System w={w} health={health} log={log} setCursor={setCursor} frameUrl={paused ? null : frameUrl} />
          <Section title="Display">
            <div className="setting">
              <span id="anim-label">Animations</span>
              <Switch.Root
                className="switch"
                checked={animationsOn}
                onCheckedChange={(on) => setMotionChoice(on === !systemReduce ? 'system' : on ? 'on' : 'off')}
                aria-labelledby="anim-label"
              >
                <Switch.Thumb className="switch-thumb" />
              </Switch.Root>
            </div>
            {systemReduce && (
              <p className="muted setting-note">
                {motionChoice === 'on'
                  ? 'Your system asks for less motion. Animations are on in this browser anyway.'
                  : 'Your system asks for less motion, so the panels snap instead of sliding.'}
              </p>
            )}
          </Section>
        </Sidebar>
      </div>
    </MotionScope>
  );
}

// One reduced-motion setting for both Motion and animate-ui, which keeps its own context.
function MotionScope({ setting, children }) {
  return (
    <MotionConfig reducedMotion={setting}>
      <ReducedMotionContext value={setting}>{children}</ReducedMotionContext>
    </MotionConfig>
  );
}

function Waiting() {
  const reduce = useShouldReduceMotion();
  return (
    <div className="waiting" role="status">
      {reduce ? (
        <span className="waiting-title">Waiting for telemetry</span>
      ) : (
        <ShimmeringText className="waiting-title" text="Waiting for telemetry" duration={1.6} color="#9c9ea3" shimmeringColor="#eff0f1" />
      )}
      <p>
        Start the bridge in <code>laptop/bridge</code>: <code>npm run replay:sim</code> to replay a recording, or <code>npm start</code>{' '}
        for the Pi.
      </p>
    </div>
  );
}

function Status({ connected, paused, hasData }) {
  const [kind, text] = paused
    ? ['paused', 'Paused']
    : !connected
      ? ['offline', 'Bridge offline']
      : hasData
        ? ['live', 'Live feed']
        : ['nodata', 'No data'];
  return (
    <span className="status" data-kind={kind} role="status">
      <span className="dot" aria-hidden="true" />
      {text}
    </span>
  );
}

function Section({ title, aside, children }) {
  return (
    <section className="sec">
      <div className="sec-head">
        <h3>{title}</h3>
        {aside && <span className="sec-aside">{aside}</span>}
      </div>
      {children}
    </section>
  );
}

// Left panel: what Beacon is homing on and what the wearer hears.
function Guidance({ w }) {
  const t = w.target;
  const cue = w.cue;
  const phrase = spoken(cue, t?.name);
  const conf = isNum(t?.conf) ? Math.min(Math.max(t.conf, 0), 1) : null;
  const pan = isNum(cue?.pan) ? Math.min(Math.max(cue.pan, -1), 1) : null;
  return (
    <>
      <Section title="Target" aside={t ? 'bound' : null}>
        {t ? (
          <>
            <p className="target-name">{t.name}</p>
            <div className="metric">
              <span className="metric-k">Hand to target</span>
              <span className="metric-v">
                <Num value={w.d_m} digits={2} />
                <small>m</small>
              </span>
            </div>
            <dl className="kv">
              <dt>From camera</dt>
              <dd><Num value={t.xyz_cam && Math.hypot(...t.xyz_cam)} digits={2} unit=" m" /></dd>
              <dt>Last seen</dt>
              <dd><Num value={msAgo(w.t_ns, t.last_seen_ns)} unit=" ms ago" /></dd>
              <dt>Confidence</dt>
              <dd className="with-meter">
                <span className="meter" aria-hidden="true"><span style={{ width: `${(conf ?? 0) * 100}%` }} /></span>
                <Num value={t.conf} digits={2} />
              </dd>
            </dl>
          </>
        ) : (
          <p className="muted">No target bound. Ask for an object and it appears here.</p>
        )}
      </Section>

      <Section title="What the wearer hears">
        <dl className="kv">
          <dt>Law</dt>
          <dd>{w.law ?? '–'}</dd>
          <dt>Reach ticks</dt>
          <dd>{cue?.continuous ? 'Continuous tone' : <Num value={cue?.tick_hz} digits={1} unit=" Hz" />}</dd>
          <dt>Pan</dt>
          <dd className="with-meter">
            <span className="pan" aria-hidden="true">{pan != null && <span style={{ left: `${(pan + 1) * 50}%` }} />}</span>
            {panWord(pan)}
          </dd>
        </dl>
        {phrase && <blockquote className="phrase">{phrase}</blockquote>}
      </Section>

      <Section title="Session map">
        <dl className="kv">
          <dt>Pose</dt>
          <dd>{w.pose == null ? 'not sent' : w.pose.valid === true ? 'valid' : 'lost'}</dd>
          <dt>Pose age</dt>
          <dd><Num value={isNum(w.pose?.age_ns) ? w.pose.age_ns / 1e6 : null} unit=" ms" /></dd>
          <dt>Object dots</dt>
          <dd>{worldObjects(w).length}</dd>
          <dt>Crumbs</dt>
          <dd>{crumbsToScene(w).length}</dd>
        </dl>
      </Section>
    </>
  );
}

// Right panel: process health, the kill-and-restart story, timing and the camera.
function System({ w, health, log, setCursor, frameUrl }) {
  const procs = Object.entries(health.procs ?? {});
  const up = procs.filter(([, p]) => p.alive).length;
  return (
    <>
      <Section title="Processes" aside={procs.length ? `${up} of ${procs.length} up` : null}>
        {procs.length ? (
          <ul className="procs">
            {procs.map(([name, p]) => {
              const age = msAgo(w.t_ns, p.hb_ns);
              return (
                <li key={name} data-up={p.alive}>
                  <span className="dot" aria-hidden="true" />
                  <span className="proc-name">{name}</span>
                  {/* plain text: heartbeat ages jitter every message, so rolling digits would never settle */}
                  <span className="proc-beat">{p.alive ? `beat ${isNum(age) ? Math.round(age) : '–'} ms ago` : 'down'}</span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="muted">No process heartbeats yet.</p>
        )}
      </Section>

      <Section title="Events">
        <Events log={log} setCursor={setCursor} />
      </Section>

      <Section title="Timing">
        <dl className="stats">
          <div>
            <dt>YOLO / depth</dt>
            <dd><Num value={measured(health.last_yolo_ms)} /> / <Num value={measured(health.last_depth_ms)} unit=" ms" /></dd>
          </div>
          <div>
            <dt>Vision p95</dt>
            <dd><Num value={measured(health.p95_vision_ns / 1e6)} unit=" ms" /></dd>
          </div>
          <div>
            <dt>16 ms misses</dt>
            <dd><Num value={health.timing?.misses_16ms} /></dd>
          </div>
          <div>
            <dt>Worst late</dt>
            <dd><Num value={health.timing?.worst_late_us} unit=" µs" /></dd>
          </div>
        </dl>
      </Section>

      {/* video is not kept in history, so a paused view never shows a live frame next to a past scene */}
      {frameUrl && (
        <Section title="Camera" aside="telemd preview">
          <img className="camera" src={frameUrl} alt="Latest downscaled camera frame from telemd" />
        </Section>
      )}
    </>
  );
}

// What the wearer hears right now: the spoken sentence, or the reach ticks.
// REACH comes first: guided keeps its last spoken clips after speech stops for the reach.
function Caption({ law, cue, targetName }) {
  if (law === 'REACH' && cue) {
    return (
      <p className="caption">
        {cue.continuous ? 'Continuous tone' : <>Ticks <Num value={cue.tick_hz} digits={1} unit=" Hz" /></>}, pan {panWord(cue.pan)}
      </p>
    );
  }
  const text = spoken(cue, targetName);
  if (!text) return null;
  return (
    <p className="caption">
      “<Rolling text={text} stagger={0.012} />”
    </p>
  );
}
