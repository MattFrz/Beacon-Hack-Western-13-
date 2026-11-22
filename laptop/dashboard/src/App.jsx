import { Switch } from '@animate-ui/react/primitives/base-ui/switch';
import { Button } from '@animate-ui/react/primitives/buttons/button';
import { Highlight, HighlightItem } from '@animate-ui/react/primitives/effects/highlight';
import { RollingText } from '@animate-ui/react/primitives/texts/rolling';
import { ShimmeringText } from '@animate-ui/react/primitives/texts/shimmering';
import { Tab, TabList, TabPanel } from '@animate-ui/react/primitives/react-aria/tabs';
import { SlidingNumber } from '@animate-ui/react/primitives/texts/sliding-number';
import { ReducedMotionContext, useShouldReduceMotion } from '@animate-ui/react/utils/motion';
import { MotionConfig } from 'motion/react';
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Tabs } from 'react-aria-components';
import { captionFromClips } from './clips.js';
import Events from './Events.jsx';
import { Collapse, Expand, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from './icons.jsx';
import Scene from './Scene.jsx';
import Scrubber from './Scrubber.jsx';
import Sidebar from './Sidebar.jsx';
import Tip from './Tip.jsx';
import { useTelemetry } from './useTelemetry.js';
import { crumbsToScene, targetObjectId } from './worldScene.js';

const MODES = ['LIVE', 'HOLD', 'LOST'];
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
// 0 means "not measured yet" for vision timings (no real YOLO run takes 0 ms), so show "–", not "0 ms".
const measured = (v) => (isNum(v) && v > 0 ? v : null);
const msAgo = (now, then) => (isNum(now) && isNum(then) ? (now - then) / 1e6 : null);
const plain = (v, unit = '') => (isNum(v) ? `${Math.round(v)}${unit}` : '–');
const panWord = (p) => (!isNum(p) ? '–' : p < -0.1 ? 'left' : p > 0.1 ? 'right' : 'centre');
const SHOWN_OBJECTS = 8;
// Seconds since a sighting, as words: a remembered object can be minutes old.
const agoText = (s) => (!isNum(s) ? '–' : s < 1 ? 'just now' : s < 60 ? `${s.toFixed(1)} s ago` : `${Math.round(s / 60)} min ago`);

const NARROW = '(max-width: 899px)';
const REDUCE = '(prefers-reduced-motion: reduce)';
const PANELS_KEY = 'beacon.panels';
const MOTION_KEY = 'beacon.motion';
const TAB_KEY = 'beacon.tab';
const TABS = ['guidance', 'system'];
const PI_FRESH_MS = 2000; // the Pi counts as connected while its last packet is younger than this
const SOURCES = [
  ['live', 'Live', 'Show data from the Pi'],
  ['replay', 'Replay', 'Play the recording'],
];
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

// A choice remembered per browser, a convenience only: storage may be blocked, so every call may fail.
function useStored(key, fallback, allowed) {
  const [value, setValue] = useState(() => {
    try {
      const v = localStorage.getItem(key);
      if (allowed.includes(v)) return v;
    } catch {
      /* fall through */
    }
    return fallback;
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, value);
    } catch {
      /* not remembered this time */
    }
  }, [key, value]);
  return [value, setValue];
}

// 'system' follows the OS reduced-motion setting; 'on' and 'off' override it in this browser only.
function useMotionChoice() {
  const [choice, setChoice] = useStored(MOTION_KEY, 'system', Object.keys(MOTION_SETTING));
  useEffect(() => {
    document.documentElement.dataset.motion = choice; // the CSS reduced-motion rule skips 'on'
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
  const { log, world, connected, stale, bridge, setSource } = useTelemetry();
  const [cursor, setCursor] = useState(null); // null = follow live, else the history index being viewed
  useEffect(() => setCursor(null), [bridge?.source, bridge?.replay]);
  const piFresh = Boolean(bridge?.pi && bridge.pi.age_ms < PI_FRESH_MS);
  const narrow = useMedia(NARROW);
  const systemReduce = useMedia(REDUCE);
  const [motionChoice, setMotionChoice] = useMotionChoice();
  const [panels, setPanels, setPanel] = usePanels(narrow);
  const [tab, setTab] = useStored(TAB_KEY, 'guidance', TABS);
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
          title="Guidance and system"
          keys="["
          open={panels.left}
          onOpenChange={(open) => setPanel('left', open)}
          icons={{ open: <PanelLeftOpen />, close: <PanelLeftClose /> }}
        >
          {/* React Aria tabs, animated by animate-ui: the indicator slides between tabs, the panels blur across */}
          <Tabs className="sb-tabs" selectedKey={tab} onSelectionChange={(key) => setTab(String(key))}>
            <header className="sb-head">
              <TabList aria-label="Left panel" className="tabs">
                <Tab id="guidance" className="tab">Guidance</Tab>
                <Tab id="system" className="tab">System</Tab>
              </TabList>
              <kbd>[</kbd>
            </header>
            <TabPanel id="guidance" className="sb-body">
              <Guidance w={w} />
            </TabPanel>
            <TabPanel id="system" className="sb-body">
              <DataSource bridge={bridge} piFresh={piFresh} />
              <System w={w} health={health} log={log} setCursor={setCursor} />
              <Display animationsOn={animationsOn} systemReduce={systemReduce} motionChoice={motionChoice} setMotionChoice={setMotionChoice} />
            </TabPanel>
          </Tabs>
        </Sidebar>

        <main className="stage" data-stale={!hasData}>
          <Scene key={bridge?.source === 'replay' ? bridge.replay : 'live'} world={hasData ? shown : null} />

          <div className="stage-top">
            <div className="topbar">
              <div className="brand">
                <span className="mark" aria-hidden="true" />
                Beacon
              </div>
              <div className="readout"><span>Tracking</span><b>{mode ?? '–'}</b></div>
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
                <SourceSwitch bridge={bridge} setSource={setSource} />
                <Status connected={connected} paused={paused} hasData={hasData} bridge={bridge} piFresh={piFresh} />
                <Tip label={focused ? 'Bring the panels back' : 'Focus the 3D view'} keys="Ctrl B">
                  <Button className="icon-btn" aria-label={focused ? 'Show the panels' : 'Focus the 3D view'} aria-pressed={focused} onClick={toggleFocus}>
                    {focused ? <Collapse /> : <Expand />}
                  </Button>
                </Tip>
              </div>
            </div>
            {bridge?.source === 'replay' && bridge.recordings?.length > 0 && (
              <label className="recording-picker">Recording
                <select value={bridge.replay} onChange={e => setSource('replay', e.target.value)}>
                  {bridge.recordings.map(({ id, label }) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
            )}
          </div>

          {!connected && log.items.length === 0 && <Waiting />}
          {connected && bridge?.source === 'live' && !hasData && !paused && <WaitingForPi bridge={bridge} setSource={setSource} />}

          <div className="stage-foot">
            <Caption law={w.law} cue={w.cue} targetName={w.target?.name} />
            <Scrubber log={log} cursor={cursor} setCursor={setCursor} replay={bridge?.source === 'replay'} />
          </div>
        </main>

        <Sidebar
          side="right"
          title="Camera"
          keys="]"
          open={panels.right}
          onOpenChange={(open) => setPanel('right', open)}
          icons={{ open: <PanelRightOpen />, close: <PanelRightClose /> }}
        >
          <header className="sb-head">
            <h2>Camera</h2>
            <kbd>]</kbd>
          </header>
          <div className="sb-body">
            <Camera paused={paused} recording={bridge?.source === 'replay' && bridge.recordings?.find(r => r.id === bridge.replay)} />
          </div>
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

function WaitingTitle({ text }) {
  const reduce = useShouldReduceMotion();
  return reduce ? (
    <span className="waiting-title">{text}</span>
  ) : (
    <ShimmeringText className="waiting-title" text={text} duration={1.6} color="#9c9ea3" shimmeringColor="#eff0f1" />
  );
}

function Waiting() {
  return (
    <div className="waiting" role="status">
      <WaitingTitle text="Waiting for the bridge" />
      <p>
        Start it in <code>laptop/bridge</code> with <code>npm start</code>. It listens for the Pi and can also play the
        recording.
      </p>
    </div>
  );
}

// Live is selected but nothing is arriving: say what the bridge last heard and how to point the Pi at this laptop.
function WaitingForPi({ bridge, setSource }) {
  const { pi, listen } = bridge;
  return (
    <div className="waiting" role="status">
      <WaitingTitle text="Waiting for the Pi" />
      <p>
        {pi
          ? `The last packet came from ${pi.address} ${agoText(pi.age_ms / 1000)}.`
          : `Nothing has arrived on UDP ${listen.port} yet.`}{' '}
        On the Pi, send <code>telemd</code> to this laptop:
      </p>
      {listen.addresses.length > 0 ? (
        <ul className="addrs">
          {listen.addresses.map((a) => (
            <li key={a.address}>
              <code>telemd/build/telemd {a.address}</code>
              <span>{a.adapter}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>This laptop has no network address yet. Join the Pi's Wi-Fi first.</p>
      )}
      {bridge.replay && (
        <Button className="btn" onClick={() => setSource('replay')}>
          Play the recording instead
        </Button>
      )}
    </div>
  );
}

// Live or Replay: asks the bridge to switch; one animate-ui Highlight slides to the source it confirms.
function SourceSwitch({ bridge, setSource }) {
  const current = bridge?.source ?? null;
  return (
    <div role="group" aria-label="Data source">
      <Highlight mode="parent" controlledItems value={current} click={false} className="src-hl" containerClassName="sources">
        {SOURCES.map(([key, label, tip]) => (
          <HighlightItem key={key} value={key}>
            <Tip label={key === 'replay' && bridge?.replay ? `${tip}: ${bridge.replay}` : tip}>
              <button
                type="button"
                className="src"
                aria-pressed={current === key}
                disabled={!bridge || (key === 'replay' && !bridge.replay)}
                onClick={() => setSource(key)}
              >
                {label}
              </button>
            </Tip>
          </HighlightItem>
        ))}
      </Highlight>
    </div>
  );
}

function Status({ connected, paused, hasData, bridge, piFresh }) {
  const pi = bridge?.pi;
  const piName = pi?.adapter === 'this laptop' ? 'Simulator on this laptop' : pi?.adapter ? `Pi via ${pi.adapter}` : `Pi at ${pi?.address}`;
  const [kind, text, detail] = paused
    ? ['paused', 'Paused']
    : !connected
      ? ['offline', 'Bridge offline']
      : bridge?.source === 'replay'
        ? ['replay', 'Recording', `Playing ${bridge.replay}`]
        : bridge?.source === 'live'
          ? piFresh
            ? ['live', piName, `Raspberry Pi at ${pi.address}${pi.adapter ? `, via ${pi.adapter}` : ''}`]
            : ['nodata', 'Waiting for the Pi']
          : hasData
            ? ['live', 'Live feed']
            : ['nodata', 'No data'];
  return (
    <span className="status" data-kind={kind} role="status" title={detail}>
      <span className="dot" aria-hidden="true" />
      {text}
    </span>
  );
}

// System tab: where the data comes from, and how the Pi reaches this laptop.
function DataSource({ bridge, piFresh }) {
  if (!bridge) return null;
  const { pi, listen } = bridge;
  return (
    <Section title="Data source" aside={bridge.source === 'live' ? (piFresh ? 'Pi connected' : 'waiting') : 'replay'}>
      <dl className="kv">
        <dt>Showing</dt>
        <dd>{bridge.source === 'live' ? 'live from the Pi' : bridge.replay}</dd>
        <dt>Pi</dt>
        <dd className="with-dot">
          <span className="dot" data-on={piFresh} aria-hidden="true" />
          {pi ? pi.address : 'not heard yet'}
        </dd>
        <dt>Network</dt>
        <dd>{pi?.adapter ?? '–'}</dd>
        <dt>Last packet</dt>
        <dd>{pi ? agoText(pi.age_ms / 1000) : '–'}</dd>
        <dt>Listening on</dt>
        <dd>UDP {listen.port}</dd>
      </dl>
      {listen.addresses.length > 0 && (
        <p className="muted setting-note">
          This laptop: {listen.addresses.map((a) => `${a.address} (${a.adapter})`).join(', ')}
        </p>
      )}
    </Section>
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
  // What the session remembers, newest sighting first (only replays joined with percept's stream carry objects today).
  const objects = (w.objects ?? []).filter((o) => o?.name).sort((a, b) => (b.last_seen_ns ?? 0) - (a.last_seen_ns ?? 0));
  const targetId = targetObjectId(w);
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
              <dd><Ago ms={msAgo(w.t_ns, t.last_seen_ns)} /></dd>
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

      <Section title="Session map" aside={objects.length ? `${objects.length} remembered` : null}>
        <dl className="kv">
          <dt>Pose</dt>
          <dd>{w.pose == null ? 'not sent' : w.pose.valid !== true ? 'lost' : w.pose.interpolated ? 'valid, interpolated' : 'valid'}</dd>
          <dt>Pose age</dt>
          <dd><Num value={isNum(w.pose?.age_ns) ? w.pose.age_ns / 1e6 : null} unit=" ms" /></dd>
          <dt>Crumbs</dt>
          <dd>{crumbsToScene(w).length}</dd>
        </dl>
        {objects.length > 0 && (
          <ul className="objs" aria-label="Remembered objects, newest sighting first">
            {objects.slice(0, SHOWN_OBJECTS).map((o) => {
              const id = o.id ?? o.name;
              const far = Array.isArray(o.xyz_cam) && o.xyz_cam.every(isNum) ? `${Math.hypot(...o.xyz_cam).toFixed(1)} m` : '–';
              const seen = o.in_latest_boxes === true ? 'in view' : agoText(msAgo(w.t_ns, o.last_seen_ns) / 1000);
              return (
                <li key={id} data-live={o.in_latest_boxes === true} data-target={id === targetId}>
                  <span className="dot" aria-hidden="true" />
                  <span className="obj-name">
                    {o.name}
                    {id === targetId && <em>target</em>}
                  </span>
                  <span className="obj-meta">{far} · {seen}</span>
                </li>
              );
            })}
          </ul>
        )}
        {objects.length > SHOWN_OBJECTS && <p className="muted more">and {objects.length - SHOWN_OBJECTS} more</p>}
      </Section>
    </>
  );
}

// Right panel: process health, the kill-and-restart story and timing.
function System({ w, health, log, setCursor }) {
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
            {/* plain text: these change with every frame, so rolling digits would never settle */}
            <dd>{plain(measured(health.last_yolo_ms))} / {plain(measured(health.last_depth_ms), ' ms')}</dd>
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
    </>
  );
}

// Show full-rate camera capture separately from the slower object and depth inference preview.
function Camera({ paused, recording }) {
  const [frames, setFrames] = useState({});
  useEffect(() => {
    const staleTimers = {};
    const onFrame = ({ detail: { channel, frame } }) => {
      setFrames((current) => ({ ...current, [channel]: frame }));
      clearTimeout(staleTimers[channel]);
      staleTimers[channel] = setTimeout(() => {
        setFrames((current) => current[channel]?.at === frame.at ? { ...current, [channel]: null } : current);
      }, channel === 'raw' ? 2000 : 3500);
    };
    const onClear = () => {
      for (const timer of Object.values(staleTimers)) clearTimeout(timer);
      setFrames({});
    };
    window.addEventListener('beacon:frame', onFrame);
    window.addEventListener('beacon:frames-clear', onClear);
    return () => {
      window.removeEventListener('beacon:frame', onFrame);
      window.removeEventListener('beacon:frames-clear', onClear);
      for (const timer of Object.values(staleTimers)) clearTimeout(timer);
    };
  }, []);
  const rawUrl = frames.raw?.url;
  const compositeUrl = frames.composite?.url;
  if (recording && !recording.video) return <p className="muted camera-note">This hand simulation contains 3D telemetry only.</p>;
  // video is not kept in history, so a paused view never shows a live frame next to a past scene
  if (paused) return <p className="muted camera-note">The camera hides while the view is paused: video is not kept in history.</p>;
  if (!rawUrl && !compositeUrl) {
    return (
      <p className="muted camera-note">
        {recording ? 'Waiting for the recorded frame.' : 'Waiting for camera frames from the Pi.'}
      </p>
    );
  }
  const views = [
    { title: 'Camera · up to 24 fps', url: rawUrl, alt: 'Live camera feed' },
    { title: 'Object detection', url: compositeUrl, crop: 'top', alt: 'Camera feed with detection boxes and labels' },
    { title: 'Depth map', url: compositeUrl, crop: 'bottom', alt: 'Colorized depth map from the camera' },
  ];
  return (
    <div className="camera-stack">
      {views.map(({ title, url, crop, alt }) => (
        <section className="camera-view" key={title}>
          <h3>{title}</h3>
          {url ? (
            crop ? (
              <div className={`camera-crop camera-crop-${crop}`}>
                <img className="camera-crop-image" src={url} alt={alt} />
              </div>
            ) : <img className="camera" src={url} alt={alt} />
          ) : <p className="muted camera-wait">{recording ? 'Not included in this recording.' : 'Waiting for this feed.'}</p>}
        </section>
      ))}
    </div>
  );
}

// The animations switch: follows the OS reduced-motion setting unless the viewer overrides it here.
function Display({ animationsOn, systemReduce, motionChoice, setMotionChoice }) {
  return (
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
  );
}

// Milliseconds under a second, seconds above, so a stale sighting never reads "10678 ms ago".
function Ago({ ms }) {
  if (!isNum(ms)) return '–';
  return ms < 1000 ? <Num value={ms} unit=" ms ago" /> : <Num value={ms / 1000} digits={1} unit=" s ago" />;
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
