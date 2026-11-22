import { Button } from '@animate-ui/react/primitives/buttons/button';
import { ChevronLeft, ChevronRight } from './icons.jsx';
import Tip from './Tip.jsx';

// Timeline over the world-state history. cursor is null while following live, else the index being viewed.
// Dragging to the end, stepping past it, or pressing Go live returns to live.
export default function Scrubber({ log, cursor, setCursor, replay }) {
  const { first, items } = log;
  if (items.length < 2) return <div className="scrubber is-empty">History builds here as telemetry arrives</div>;

  const newest = first + items.length - 1;
  const index = cursor == null ? newest : Math.min(newest, Math.max(cursor, first));
  const go = (i) => setCursor(i >= newest ? null : Math.max(i, first));
  const viewed = items[index - first];
  const back = (viewed.at - items.at(-1).at) / 1000;
  const bounds = replay && __REPLAY_BOUNDS__[replay];
  const elapsed = bounds && Number.isFinite(viewed.world.t_ns)
    ? Math.max(0, Math.min(bounds[1], viewed.world.t_ns) - bounds[0]) / 1e9 : null;
  const piTime = typeof viewed.world.t_ns === 'number' ? `Pi t ${(viewed.world.t_ns / 1e9).toFixed(3)} s` : null;

  return (
    <div className="scrubber" data-paused={cursor != null}>
      <Tip label="Previous message" side="top">
        <Button className="icon-btn" aria-label="Previous message" onClick={() => go(index - 1)} disabled={index <= first}>
          <ChevronLeft />
        </Button>
      </Tip>
      <Tip label="Next message" side="top">
        <Button className="icon-btn" aria-label="Next message" onClick={() => go(index + 1)} disabled={cursor == null}>
          <ChevronRight />
        </Button>
      </Tip>
      <input type="range" className="slider" aria-label="Buffered history position"
        min={first} max={newest} value={index} step={1}
        onChange={e => go(e.currentTarget.valueAsNumber)} />
      <span className="scrub-label">
        {elapsed != null ? (
          `Replay \u00b7 ${elapsed.toFixed(1)} / ${((bounds[1] - bounds[0]) / 1e9).toFixed(1)} s`
        ) : cursor == null ? (
          replay ? 'Playing recording' : 'Following live'
        ) : (
          <>
            {back.toFixed(1)} s{piTime && <em>{piTime}</em>}
          </>
        )}
      </span>
      <Button className="btn" data-variant="primary" onClick={() => setCursor(null)} disabled={cursor == null}>
        {replay ? 'Resume replay' : 'Go live'}
      </Button>
    </div>
  );
}
