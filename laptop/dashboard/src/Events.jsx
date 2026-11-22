import { useMemo } from 'react';
import { eventsFromLog } from './events.js';

const SHOWN = 8;
const clock = (at) => new Date(performance.timeOrigin + at).toLocaleTimeString([], { hour12: false });

// Kills, restarts and mode changes, newest last. Click one to scrub the view to that moment.
export default function Events({ log, setCursor }) {
  const events = useMemo(() => eventsFromLog(log.items, log.first), [log]);
  if (!events.length) return <p className="muted">No kills or mode changes yet</p>;
  return (
    <ol className="events">
      {events.slice(-SHOWN).map((e) => (
        <li key={`${e.index} ${e.text}`} className={e.kind}>
          <button type="button" onClick={() => setCursor(e.index)}>
            <span>{e.text}</span>
            <time>{clock(e.at)}</time>
          </button>
        </li>
      ))}
    </ol>
  );
}
