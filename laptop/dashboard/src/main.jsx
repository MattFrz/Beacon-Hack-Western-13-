import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import { Tooltip } from '@animate-ui/react/primitives/base-ui/tooltip';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

// Fonts are bundled, not fetched: the laptop may sit on the Pi's hotspot with no internet.
// Reduced motion is decided in App, which lets the viewer override the system setting.
createRoot(document.getElementById('root')).render(
  <Tooltip.Provider delay={250}>
    <App />
  </Tooltip.Provider>,
);
