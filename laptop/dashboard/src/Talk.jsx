import { useRef, useState } from 'react';

// Push-to-talk for the demo: hold the button (or Space), say "where's my water bottle", let go.
// The browser turns speech into text (Chrome / Edge; Web Speech API), the bridge forwards the text to
// `beacon_cmd --udp` on the Pi, which does the word matching and writes the intent. Speech-to-text is on
// this laptop, not the Pi; everything after it is on the Pi. Typing in the box and pressing Enter works too.
const Recognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);

export default function Talk({ say, said, connected }) {
  const [heard, setHeard] = useState('');
  const [listening, setListening] = useState(false);
  const [typed, setTyped] = useState('');
  const rec = useRef(null);
  const finalText = useRef('');

  const start = () => {
    if (!Recognition || listening) return;
    const r = new Recognition();
    r.lang = 'en-US';
    r.interimResults = true;
    r.continuous = true;
    finalText.current = '';
    r.onresult = (e) => {
      let text = '';
      for (const res of e.results) text += res[0].transcript;
      finalText.current = text;
      setHeard(text);
    };
    r.onerror = (e) => setHeard(`(mic error: ${e.error})`);
    r.onend = () => {
      setListening(false);
      const text = finalText.current.trim();
      if (text) say(text);
    };
    rec.current = r;
    setHeard('');
    setListening(true);
    r.start();
  };
  const stop = () => rec.current?.stop();

  const send = (e) => {
    e.preventDefault();
    if (!typed.trim()) return;
    setHeard(typed.trim());
    say(typed.trim());
    setTyped('');
  };

  const status = !connected
    ? 'bridge offline'
    : said?.error
      ? `not sent: ${said.error}`
      : said && said.age_ms < 10000
        ? `sent to ${said.to}`
        : '';

  return (
    <div className="talk">
      <button
        type="button"
        className={listening ? 'btn talk-btn on' : 'btn talk-btn'}
        disabled={!Recognition || !connected}
        title={Recognition ? 'Hold and speak, e.g. "where\'s my water bottle"' : 'Speech needs Chrome or Edge'}
        onPointerDown={start}
        onPointerUp={stop}
        onPointerLeave={() => listening && stop()}
      >
        {listening ? 'Listening…' : 'Hold to talk'}
      </button>
      <form onSubmit={send}>
        <input
          className="talk-input"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          placeholder="or type: find bottle"
          disabled={!connected}
        />
      </form>
      {(heard || status) && (
        <span className="talk-heard">
          {heard && <q>{heard}</q>} {status && <em>{status}</em>}
        </span>
      )}
    </div>
  );
}
