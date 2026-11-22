import { Button } from '@animate-ui/react/primitives/buttons/button';
import * as SidebarPrimitive from '@animate-ui/react/primitives/sidebar';
import { useEffect } from 'react';
import Tip from './Tip.jsx';

// Below 768px the primitive's TriggerIcon reads its mobile-sheet state, which this layout never opens: mirror ours into it.
function SyncMobile({ open }) {
  const { setOpenMobile } = SidebarPrimitive.useSidebar();
  useEffect(() => setOpenMobile(open), [open, setOpenMobile]);
  return null;
}

// One animate-ui sidebar per side. Gap keeps the panel's width in the row, so the 3D view widens as the
// panel closes; Container slides the fixed panel and its handle on the same timing (0 ms under reduced
// motion); TriggerIcon swaps the handle's icon. The open state lives in App, which owns the shortcuts.
export default function Sidebar({ side, open, onOpenChange, title, keys, icons, children }) {
  const id = `panel-${side}`;
  const edge = (offset) => ({ [side]: open ? `calc(var(--sb-w) + ${offset})` : offset });
  return (
    <SidebarPrimitive.Provider open={open} onOpenChange={onOpenChange} className="sb-provider">
      <SyncMobile open={open} />
      <SidebarPrimitive.Gap className="sb-gap" style={{ width: open ? 'var(--sb-w)' : 0 }} />

      <SidebarPrimitive.Container
        id={id}
        className="sb"
        data-side={side}
        role="complementary"
        aria-label={title}
        inert={!open}
        style={{ [side]: open ? 0 : 'calc(var(--sb-w) * -1)' }}
      >
        <header className="sb-head">
          <h2>{title}</h2>
          <kbd>{keys}</kbd>
        </header>
        <div className="sb-body">{children}</div>
      </SidebarPrimitive.Container>

      <SidebarPrimitive.Container className="sb-handle" data-side={side} style={edge('var(--gutter)')}>
        <Tip label={`${open ? 'Hide' : 'Show'} ${title.toLowerCase()}`} keys={keys} side={side === 'left' ? 'right' : 'left'}>
          <Button
            className="icon-btn"
            aria-label={`${open ? 'Hide' : 'Show'} ${title.toLowerCase()} panel`}
            aria-expanded={open}
            aria-controls={id}
            onClick={() => onOpenChange(!open)}
          >
            <SidebarPrimitive.TriggerIcon open={icons.close} closed={icons.open} />
          </Button>
        </Tip>
      </SidebarPrimitive.Container>
    </SidebarPrimitive.Provider>
  );
}
