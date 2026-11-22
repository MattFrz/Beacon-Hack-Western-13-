import { Highlight, HighlightItem } from '@animate-ui/react/primitives/effects/highlight';
import { useMemo } from 'react';
import { eventsFromLog } from './events.js';

const SHOWN = 8;
const clock = (at) => new Date(performance.timeOrigin + at).toLocaleTimeString([], { hour12: false });

// Kills, restarts and mode changes as a timeline, newest last. Click one to scrub the view to that moment;
// one animate-ui Highlight glides behind the row under the pointer.
export default function Events({ log, setCursor }) {
  const events = useMemo(() => eventsFromLog(log.items, log.first), [log]);
  if (!events.length) return <p className="muted">No kills or mode changes yet.</p>;
  return (
    <ol className="timeline">
      <Highlight mode="children" controlledItems hover click={false} className="row-hl">
        {events.slice(-SHOWN).map((e) => {
          const key = `${e.index} ${e.text}`;
          return (
            <HighlightItem key={key} value={key} as="li" data-kind={e.kind}>
              <button type="button" onClick={() => setCursor(e.index)} aria-label={`${e.text}, at ${clock(e.at)}. Show this moment.`}>
                <span className="tl-dot" aria-hidden="true" />
                <span className="tl-text">{e.text}</span>
                <time>{clock(e.at)}</time>
              </button>
            </HighlightItem>
          );
        })}
      </Highlight>
    </ol>
  );
}
