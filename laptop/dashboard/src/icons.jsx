// Small stroke icons (24-unit grid, currentColor), drawn inline so the dashboard works offline.
const Icon = ({ children }) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

const Panel = ({ x, children }) => (
  <Icon>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <path d={`M${x} 3v18`} />
    {children}
  </Icon>
);

export const PanelLeftClose = () => <Panel x={9}><path d="m16 15-3-3 3-3" /></Panel>;
export const PanelLeftOpen = () => <Panel x={9}><path d="m14 9 3 3-3 3" /></Panel>;
export const PanelRightClose = () => <Panel x={15}><path d="m8 9 3 3-3 3" /></Panel>;
export const PanelRightOpen = () => <Panel x={15}><path d="m10 15-3-3 3-3" /></Panel>;

export const Expand = () => (
  <Icon>
    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
  </Icon>
);
export const Collapse = () => (
  <Icon>
    <path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7" />
  </Icon>
);
export const ChevronLeft = () => <Icon><path d="m15 18-6-6 6-6" /></Icon>;
export const ChevronDown = () => <Icon><path d="m6 9 6 6 6-6" /></Icon>;
export const ChevronRight = () => <Icon><path d="m9 18 6-6-6-6" /></Icon>;
