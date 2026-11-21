import { Slider } from '@animate-ui/react/primitives/base-ui/slider';
import { Button } from '@animate-ui/react/primitives/buttons/button';

// Timeline over the world-state history. cursor is null while following live, else the index being viewed.
// Dragging to the end, stepping past it, or pressing Live returns to live.
export default function Scrubber({ log, cursor, setCursor }) {
  const { first, items } = log;
  if (items.length < 2) return <div className="scrubber muted">History appears here as telemetry arrives</div>;

  const newest = first + items.length - 1;
  const index = cursor == null ? newest : Math.max(cursor, first);
  const go = (i) => setCursor(i >= newest ? null : Math.max(i, first));
  const viewed = items[index - first];
  const back = (viewed.at - items.at(-1).at) / 1000;
  const piTime = typeof viewed.world.t_ns === 'number' ? ` · Pi t ${(viewed.world.t_ns / 1e9).toFixed(3)} s` : '';

  return (
    <div className={cursor == null ? 'scrubber' : 'scrubber paused'}>
      <Button className="scrub-btn" aria-label="Previous message" onClick={() => go(index - 1)} disabled={index <= first}>
        ◀
      </Button>
      <Button className="scrub-btn" aria-label="Next message" onClick={() => go(index + 1)} disabled={cursor == null}>
        ▶
      </Button>
      <Slider.Root className="slider" min={first} max={newest} value={index} onValueChange={(v) => go(v)}>
        <Slider.Control className="slider-control">
          <Slider.Track className="slider-track">
            <Slider.Indicator className="slider-indicator" />
            <Slider.Thumb className="slider-thumb" aria-label="Replay position" />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <span className="scrub-label">{cursor == null ? 'following live' : `${back.toFixed(1)} s${piTime}`}</span>
      <Button className="scrub-btn" onClick={() => setCursor(null)} disabled={cursor == null}>
        Live
      </Button>
    </div>
  );
}
