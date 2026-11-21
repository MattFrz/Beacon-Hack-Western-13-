// Usage: node main.js          live: telemd -> UDP 5005 -> ws://127.0.0.1:8765, recorded to recordings/
//        node main.js <file>   loop a .json or .jsonl file instead (no Pi needed)
import { fileURLToPath } from 'node:url';
import { startBridge } from './bridge.js';

const replayFile = process.argv[2];
try {
  const bridge = await startBridge({
    wsPort: 8765,
    udpPort: 5005,
    recordDir: fileURLToPath(new URL('recordings/', import.meta.url)),
    replayFile,
  });
  console.log(`bridge: dashboards connect to ws://127.0.0.1:${bridge.wsPort}`);
  console.log(replayFile
    ? `bridge: replaying ${replayFile} in a loop`
    : `bridge: telemd sends to UDP ${bridge.udpPort} on this laptop; recording to ${bridge.file}`);
} catch (err) {
  console.error(`bridge: ${err.message}`);
  process.exit(1);
}
