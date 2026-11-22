import { Slider } from '@animate-ui/react/primitives/base-ui/slider';
import { Button } from '@animate-ui/react/primitives/buttons/button';
import { ChevronLeft, ChevronRight } from './icons.jsx';
import Tip from './Tip.jsx';

// Timeline over the world-state history. cursor is null while following live, else the index being viewed.
// Dragging to the end, stepping past it, or pressing Go live returns to live.
export default function Scrubber({ log, cursor, setCursor }) {
  const { first, items } = log;
  if (items.length < 2) return <div className="scrubber is-empty">History builds here as telemetry arrives</div>;

  const newest = first + items.length - 1;
  const index = cursor == null ? newest : Math.max(cursor, first);
  const go = (i) => setCursor(i >= newest ? null : Math.max(i, first));
  const viewed = items[index - first];
  const back = (viewed.at - items.at(-1).at) / 1000;
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
      <Slider.Root className="slider" min={first} max={newest} value={index} onValueChange={(v) => go(v)}>
        <Slider.Control className="slider-control">
          <Slider.Track className="slider-track">
            <Slider.Indicator className="slider-indicator" />
            <Slider.Thumb className="slider-thumb" aria-label="Replay position" />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <span className="scrub-label">
        {cursor == null ? (
          'Following live'
        ) : (
          <>
            {back.toFixed(1)} s{piTime && <em>{piTime}</em>}
          </>
        )}
      </span>
      <Button className="btn" data-variant="primary" onClick={() => setCursor(null)} disabled={cursor == null}>
        Go live
      </Button>
    </div>
  );
}
