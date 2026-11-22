// Usage: node main.js                      live: telemd -> UDP 5005 -> ws://127.0.0.1:8765, recorded to recordings/;
//                                          the vid360 recording is loaded too, for the dashboard's Replay switch
//        node main.js <file> [--frames DIR] start on that replay instead (no Pi needed); live still listens
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startBridge } from './bridge.js';

const sample = (name) => fileURLToPath(new URL(`../samples/${name}`, import.meta.url));
const argFile = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : undefined;
// --frames DIR: optional composite preview JPEGs (probe --frames-dir) replayed in sync.
const framesFlag = process.argv.indexOf('--frames');
const recordings = [
  { id: 'vid360', label: 'Camera look-around', file: sample('vid360-look-around.jsonl'), framesDir: sample('vid360-frames') },
  { id: 'reach', label: 'Hand reaching for keys', file: sample('sim-reach-lost.jsonl') },
];
const replayFile = argFile && path.resolve(argFile);
const framesDir = framesFlag > -1 ? process.argv[framesFlag + 1] : undefined;
const selected = recordings.find(entry => entry.file === replayFile);
if (selected && framesDir) selected.framesDir = framesDir;

try {
  const bridge = await startBridge({
    wsPort: 8765,
    udpPort: 5005,
    recordDir: fileURLToPath(new URL('recordings/', import.meta.url)),
    replayFile,
    recordings,
    framesDir,
    source: argFile ? 'replay' : 'live',
  });
  console.log(`bridge: dashboards connect to ws://127.0.0.1:${bridge.wsPort}`);
  console.log(`bridge: telemd sends to UDP ${bridge.udpPort} on this laptop; live sessions are recorded to ${bridge.file}`);
  console.log(argFile ? `bridge: replaying ${argFile}` : 'bridge: live, both demo recordings available');
} catch (err) {
  console.error(`bridge: ${err.message}`);
  process.exit(1);
}
