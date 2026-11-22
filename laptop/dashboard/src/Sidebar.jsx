import { Button } from '@animate-ui/react/primitives/buttons/button';
import * as SidebarPrimitive from '@animate-ui/react/primitives/sidebar';
import { useEffect, useState } from 'react';
import Tip from './Tip.jsx';

// Below 768px the primitive's TriggerIcon reads its mobile-sheet state, which this layout never opens: mirror ours into it.
function SyncMobile({ open }) {
  const { setOpenMobile } = SidebarPrimitive.useSidebar();
  useEffect(() => setOpenMobile(open), [open, setOpenMobile]);
  return null;
}

export function usePanelWidth(side) {
  const storageKey = `beacon.width.${side}`;
  const [preferred, setPreferred] = useState(() => {
    try {
      const saved = Number(localStorage.getItem(storageKey));
      if (Number.isFinite(saved) && saved >= 260) return saved;
    } catch { /* Storage is optional. */ }
    return side === 'left' ? 320 : 440;
  });
  useEffect(() => {
    try { localStorage.setItem(storageKey, String(preferred)); } catch { /* Storage is optional. */ }
  }, [preferred, storageKey]);
  return [preferred, setPreferred];
}

export default function Sidebar({ side, open, onOpenChange, title, keys, icons, children, preferred, limit, setWidth }) {
  const id = `panel-${side}`;
  const pixels = Math.min(preferred, limit);
  const width = `${pixels}px`;
  const resize = value => setWidth(Math.min(limit, Math.max(260, Math.round(value))));
  const fromEdge = x => side === 'left' ? x : window.innerWidth - x;
  const edge = (offset) => ({ [side]: open ? `calc(${width} + ${offset})` : offset });
  return (
    <SidebarPrimitive.Provider open={open} onOpenChange={onOpenChange} className="sb-provider">
      <SyncMobile open={open} />
      <SidebarPrimitive.Gap className="sb-gap" style={{ width: open ? width : 0 }} />

      <SidebarPrimitive.Container
        id={id}
        className="sb"
        data-side={side}
        role="complementary"
        aria-label={title}
        inert={!open}
        style={{ width, [side]: open ? 0 : `calc(${width} * -1)` }}
      >
        {children}
        <div className="panel-resizer" role="separator" tabIndex={0} aria-orientation="vertical"
          aria-label={`Resize ${title}`} aria-controls={id} aria-valuemin={Math.min(260, limit)}
          aria-valuemax={limit}
          aria-valuenow={pixels}
          onPointerDown={e => { if (e.button === 0) e.currentTarget.setPointerCapture(e.pointerId); }}
          onPointerMove={e => { if (e.currentTarget.hasPointerCapture(e.pointerId)) resize(fromEdge(e.clientX)); }}
          onKeyDown={e => {
            if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
            e.preventDefault();
            const delta = (e.key === 'ArrowRight') === (side === 'left') ? 16 : -16;
            resize(e.currentTarget.parentElement.getBoundingClientRect().width + delta);
          }} />
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
