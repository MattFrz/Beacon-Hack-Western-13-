// Usage: node main.js                      live: telemd -> UDP 5005 -> ws://127.0.0.1:8765, recorded to recordings/;
//                                          the vid360 recording is loaded too, for the dashboard's Replay switch
//        node main.js <file> [--frames DIR] start on that replay instead (no Pi needed); live still listens
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { startBridge } from './bridge.js';

const sample = (name) => fileURLToPath(new URL(`../samples/${name}`, import.meta.url));
const argFile = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : undefined;
// --frames DIR: optional composite preview JPEGs (probe --frames-dir) replayed in sync.
const framesFlag = process.argv.indexOf('--frames');
const vid360 = sample('vid360-look-around.jsonl');
const replayFile = argFile ?? (fs.existsSync(vid360) ? vid360 : undefined);
const framesDir = framesFlag > -1 ? process.argv[framesFlag + 1] : argFile ? undefined : sample('vid360-frames');

try {
  const bridge = await startBridge({
    wsPort: 8765,
    udpPort: 5005,
    recordDir: fileURLToPath(new URL('recordings/', import.meta.url)),
    replayFile,
    framesDir,
    source: argFile ? 'replay' : 'live',
  });
  console.log(`bridge: dashboards connect to ws://127.0.0.1:${bridge.wsPort}`);
  console.log(`bridge: telemd sends to UDP ${bridge.udpPort} on this laptop; live sessions are recorded to ${bridge.file}`);
  console.log(argFile ? `bridge: replaying ${argFile} (switch to live in the dashboard)` : `bridge: live; the dashboard can switch to ${replayFile ?? 'no replay'}`);
} catch (err) {
  console.error(`bridge: ${err.message}`);
  process.exit(1);
}
