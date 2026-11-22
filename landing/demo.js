const slider = document.querySelector('#reach');
const reading = document.querySelector('#reading');
const modeLabel = document.querySelector('#mode');
const cueLabel = document.querySelector('#state');
const playButton = document.querySelector('#play');
const trackingButton = document.querySelector('#tracking');
const wave = document.querySelector('.wave');

const STEADY_TONE_CM = 15;
const HOLD_MS = 1500;
let mode = 'live';
let playing = false;
let context;
let lostClip;
let source;
let tickTimer;
let holdTimer;

function distance() {
  return 60 - Number(slider.value);
}

function tickInterval(cm) {
  return 80 + (Math.max(cm, STEADY_TONE_CM) - STEADY_TONE_CM) * 16;
}

function render() {
  const cm = distance();
  const live = mode === 'live';
  reading.textContent = live ? cm + ' cm' : 'Unavailable';
  slider.disabled = !live;
  slider.setAttribute('aria-valuetext', live ? cm + ' centimetres from the keys' : 'Distance unavailable');
  wave.style.setProperty('--gap', (3 + cm / 3) + 'px');
  wave.dataset.mode = mode;
  modeLabel.dataset.mode = mode;
  const modeText = { live: 'Live', hold: 'Hold', lost: 'Lost' }[mode];
  if (modeLabel.textContent !== modeText) modeLabel.textContent = modeText;

  if (mode === 'lost') cueLabel.textContent = '“I lost the target.”';
  else if (mode === 'hold') cueLabel.textContent = 'Holding the last cue';
  else if (cm <= STEADY_TONE_CM) cueLabel.textContent = 'Steady tone';
  else cueLabel.textContent = cm < 35 ? 'Fast ticks' : 'Slow ticks';

  trackingButton.textContent = live ? 'Simulate tracking loss' : 'Restore tracking';
  playButton.textContent = playing ? 'Stop sound' : 'Play sound';
}

function silence() {
  clearTimeout(tickTimer);
  if (source) {
    source.stop();
    source = undefined;
  }
}

function playSource(node, gain) {
  source = node;
  node.connect(gain).connect(context.destination);
  node.onended = () => {
    node.disconnect();
    gain.disconnect();
    if (source === node) source = undefined;
  };
  node.start();
}

function playCue() {
  silence();
  if (!playing || context?.state !== 'running') return;

  const now = context.currentTime;
  const gain = context.createGain();
  if (mode === 'lost') {
    if (lostClip) {
      const voice = context.createBufferSource();
      voice.buffer = lostClip;
      gain.gain.value = 0.45;
      playSource(voice, gain);
    }
    return;
  }

  const cm = distance();
  const holding = mode === 'hold';
  const steady = !holding && cm <= STEADY_TONE_CM;
  const voice = context.createOscillator();
  voice.frequency.value = holding ? 400 : 620;
  gain.gain.setValueAtTime(0, now);
  gain.gain.linearRampToValueAtTime(0.06, now + 0.009);
  playSource(voice, gain);

  if (!steady) {
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.065);
    voice.stop(now + 0.07);
    tickTimer = setTimeout(playCue, tickInterval(cm) * (holding ? 1.6 : 1));
  }
}

function update() {
  render();
  playCue();
}

function stop() {
  playing = false;
  update();
}

playButton.addEventListener('click', async () => {
  if (playing) {
    stop();
    return;
  }

  playing = true;
  render();
  try {
    context ??= new AudioContext();
    await context.resume();
    if (!playing) return;
    playCue();
  } catch {
    stop();
    cueLabel.textContent = 'Audio unavailable';
  }
});

slider.addEventListener('input', update);

trackingButton.addEventListener('click', () => {
  clearTimeout(holdTimer);
  if (mode === 'live') {
    mode = 'hold';
    holdTimer = setTimeout(() => {
      mode = 'lost';
      update();
    }, HOLD_MS);
  } else {
    mode = 'live';
  }
  update();
});

async function loadLostCue() {
  try {
    const response = await fetch(new URL('assets/lost_target.wav', document.baseURI));
    if (!response.ok) return;
    const buffer = await response.arrayBuffer();
    const decoder = new OfflineAudioContext(1, 1, 16000);
    lostClip = await decoder.decodeAudioData(buffer);
    if (mode === 'lost') playCue();
  } catch {
    // The text cue remains available when the audio file cannot be decoded.
  }
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) stop();
});
window.addEventListener('pagehide', stop);
loadLostCue();
