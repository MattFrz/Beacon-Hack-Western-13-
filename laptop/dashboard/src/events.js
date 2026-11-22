// Process kills and restarts and LIVE / HOLD / LOST changes, from useTelemetry's log.items ({ at, world }).
// This is the demo's `slay percept` story in one list. `first` is log.first, so each event's index can drive the scrubber.
export function eventsFromLog(items, first = 0) {
  const events = [];
  let alive = {}; // proc name -> last known alive
  let downAt = {}; // proc name -> t_ns it went down
  let mode; // last known mode
  let lastT;

  items.forEach(({ at, world: w }, i) => {
    const t = w.t_ns;
    const push = (kind, text) => events.push({ index: first + i, at, t_ns: t, kind, text });
    // A replay loop or a Pi reboot sends the clock backwards: start over, never pair a kill with a later run's restart.
    if (typeof t !== 'number' || t < lastT) [alive, downAt, mode] = [{}, {}, undefined];
    lastT = t;

    // Messages without health or mode (telemd's target-only ones) keep the last known state instead of resetting it.
    for (const [name, p] of Object.entries(w.health?.procs ?? {})) {
      if (alive[name] === true && p.alive === false) {
        downAt[name] = t;
        push('down', `${name} down`);
      } else if (alive[name] === false && p.alive === true) {
        push('up', name in downAt ? `${name} back after ${((t - downAt[name]) / 1e9).toFixed(1)} s` : `${name} back`);
        delete downAt[name];
      }
      alive[name] = p.alive;
    }

    if (typeof w.mode === 'string' && w.mode !== mode) {
      if (mode !== undefined) {
        // While a process is down, say how long after the latest kill the mode changed: the HOLD window, then LOST.
        const since = Math.max(...Object.values(downAt));
        const label = w.mode === 'NONE' ? 'No target' : w.mode;
        push(w.mode, Number.isFinite(since) ? `${label} +${((t - since) / 1e9).toFixed(1)} s` : label);
      }
      mode = w.mode;
    }
  });
  return events;
}
