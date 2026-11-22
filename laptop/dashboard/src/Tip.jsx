import { Tooltip } from '@animate-ui/react/primitives/base-ui/tooltip';

// animate-ui tooltip around one control: the label, plus its keyboard shortcut when it has one.
export default function Tip({ label, keys, side = 'bottom', children }) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger render={children} />
      <Tooltip.Portal>
        <Tooltip.Positioner side={side} sideOffset={8} className="tip-pos">
          <Tooltip.Popup className="tip">
            {label}
            {keys && <kbd>{keys}</kbd>}
          </Tooltip.Popup>
        </Tooltip.Positioner>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
